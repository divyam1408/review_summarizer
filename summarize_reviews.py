
import argparse
import os
import prompts

from dotenv import load_dotenv
load_dotenv()

from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.prompts import ChatPromptTemplate

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from tqdm import tqdm

import utils
from structured_output import AttributeResult, ReviewResult
from pydantic import ValidationError


MODEL = "mistralai/Mistral-7B-Instruct-v0.2"

@retry(
    reraise=False,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(ValidationError),
    retry_error_callback=utils.return_none_on_failure,
)
def classify_review(review: dict, product_attributes: list[str], product_details: dict) -> ReviewResult:
  """
  Given a review and a list of product attributes, determine for EACH attribute:
  1) Whether the attribute is mentioned or clearly implied.
  2) Sentiment toward that attribute: positive, negative, mixed, neutral, or not_mentioned.
  3) A short evidence quote copied verbatim from the review that supports the  decision.
  4) Confidence score from 0.0 to 1.0.

  Args:
    review (dict): The dict containing review metadata.
    product_attributes (list[str]): The list of product attributes.
  Returns:
    ReviewResult
  """

  formatted_attributes = "\n".join([str(attribute) for attribute in product_attributes])

  print("REVIEW: \n", review)
  llm = ChatHuggingFace(
      llm=HuggingFaceEndpoint(
          repo_id="mistralai/Mistral-7B-Instruct-v0.2",
          temperature=0,
      )
  )


  prompt = ChatPromptTemplate.from_template(prompts.identify_attributes_prompt)
  chain = (
      prompt
     | llm
  )

  result = chain.invoke({
    "EXISTING_ATTRIBUTES_LIST": formatted_attributes,
    "REVIEW_TEXT": str(review),
    "PRODUCT_NAME":product_details.get("title")
  })

  result = ReviewResult.model_validate_json(result.content)
  return result


def classify_multiple_reviews(reviews: list[dict], num_reviews: int = 10) -> tuple[list[ReviewResult], list[str]]:
  """
  Classify multiple reviews.
  Args:
    reviews (list[dict]): The list of reviews.
    num_reviews (int): The number of reviews to classify.
  Returns:
    tuple[list[ReviewResult], list[str]]: The list of review results and the list of generated attributes.
  """
  
  results = []
  existing_attributes = []
  prepared_reviews = utils.prepare_reviews(reviews)
  #random.shuffle(prepared_reviews)
  prepared_reviews = prepared_reviews[:num_reviews]
  # prepared_reviews = "\n".join([str(review) for review in prepared_reviews[:num_reviews]])
  for review in tqdm(prepared_reviews):
    result = classify_review(review, existing_attributes, product)
    if result:
      for attribute in result.attributes:
        if attribute.attribute not in existing_attributes:
          existing_attributes.append(attribute.attribute)
      results.append(result)
    else:
      print('Model Output Validation Error')
    print('ATTRIBUTES:\n', existing_attributes)

  return results, existing_attributes




if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Summarize product reviews.")
  parser.add_argument("--category", type=str, default="Clothing_Shoes_and_Jewelry", help="Product category to scan.")
  parser.add_argument("--num_reviews", type=int, default=5, help="Number of reviews to classify.")
  parser.add_argument("--output_name", type=str, default="experiment_results", help="Name for the output files (without extension).")
  
  args = parser.parse_args()

  category = args.category
  num_reviews = args.num_reviews
  output_name = args.output_name

  product, reviews = utils.prepare_data(category)
  review_df = utils.reviews_to_df(reviews)
  print("============Classifying Reviews============")
  classified_reviews, existing_attributes = classify_multiple_reviews(reviews, num_reviews=num_reviews)
  print("============Aggregating Reviews============")
  aggregated_results = utils.aggregate_by_attribute(classified_reviews)
  summary_df, details_df = utils.aggregation_to_dfs(aggregated_results, review_df)
  print("============Saving Results============")
  
  output_dir = f"Results/{category}"
  os.makedirs(output_dir, exist_ok=True)

  summary_df.to_csv(f"{output_dir}/{category}_summary_{output_name}.csv", index=False)
  details_df.to_csv(f"{output_dir}/{category}_details_{output_name}.csv", index=False)

