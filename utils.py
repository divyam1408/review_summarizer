
import pandas as pd
from collections import Counter, defaultdict
from datasets import load_dataset
from typing import List, Dict, Any, Tuple
from tqdm import tqdm

from structured_output import ReviewResult



def prepare_data(category: str, scan_reviews: int = 100000, min_reviews:int = 100) -> tuple[dict, list] :
  """
  This function uses McAuley-Lab/Amazon-Reviews-2023 dataset to return the most common product and its reviews under a given category.
  Args:
    category (str): The category to scan.
    scan_reviews (int): The number of reviews to scan.
    min_reviews (int): The minimum number of reviews for the most common product.
  Returns:
    most_common_product (dict): The dict contianing product metadata.
    reviews (list): The dict containing reviews.
  """

  # scan_reviews = 100000
  top_k_products = 1
  # min_review = 100
  count = Counter()
  reviews = defaultdict(list)
  CATEGORY = category

  reviews_stream = load_dataset(
      "McAuley-Lab/Amazon-Reviews-2023",
      f"raw_review_{CATEGORY}",
      split="full",
      streaming=True,
      trust_remote_code=True,

  )

  product_stream = load_dataset(
      "McAuley-Lab/Amazon-Reviews-2023",
      f"raw_meta_{CATEGORY}",
      split="full",
      streaming=True,
      trust_remote_code=True,

  )

  reviews_stream = reviews_stream.shuffle(seed=42, buffer_size=200_000)
  reviews_stream = list(reviews_stream.take(scan_reviews))

  for i, review in tqdm(enumerate(reviews_stream)):
    product_id = review.get("parent_asin")
    if product_id:
      count[product_id] += 1
      reviews[product_id].append(review)
    if i + 1 >= scan_reviews:
      break

  most_common_product_id = count.most_common(1)[-1][0]
  most_common_product_metadata = None
  if count.most_common(1)[-1][1] < min_reviews:
    raise ValueError("Not Enough Reviews!!! Select another category or increase number of reviews to scan.")

  print("=========== Get product Metadata ===========")
  for meta in tqdm(product_stream):
    if meta.get("parent_asin") == most_common_product_id:
      most_common_product_metadata = meta
      break

  if most_common_product_metadata is None:
    raise ValueError("Product metadata not found!")
  print("CATEGRY:\n", most_common_product_metadata["main_category"])
  print(f"PRODUCT: {most_common_product_metadata["title"]} NUMBER_OF_REVIEWS: {count.most_common(1)[-1][1]}")
  print("RATING DISTRIBUTION:", Counter(Counter([review.get('rating') for review in reviews[most_common_product_id]])))
  return most_common_product_metadata, reviews[most_common_product_id]


def reviews_to_df(
  reviews_raw: List[Dict[str, Any]],
) -> pd.DataFrame:
  """
  Convert raw review JSONs into a DataFrame keyed by review_id (= timestamp).
  """
  rows = []
  for r in reviews_raw:
      rows.append({
          "review_id": str(r.get("timestamp")),  # normalize to string
          "review_title": r.get("title"),
          "review_text": r.get("text"),
          "review_rating": r.get("rating"),
      })

  df = pd.DataFrame(rows)

  # Compute text length for tie-breaking
  df["_text_len"] = df["review_text"].astype(str).str.len()

  # Keep longest review per review_id
  df = (
      df.sort_values("_text_len", ascending=False)
        .drop_duplicates(subset="review_id", keep="first")
        .drop(columns="_text_len")
        .reset_index(drop=True)
  )
  return df

def prepare_reviews(reviews: list[dict], max_review_words: int = 100) -> list[dict]:

  """Prepare reviews to be consumed in pipeline.
  Following processing is done:
  1) Remove reviews with more than 100 words.
  2) Remove reviews with no title or text.
  3) Keep necessary attributes for a review (review_id, review_title, review_text)
  Args:
    reviews (list[dict]): The list of reviews.
  Returns:
    list[dict]: The list of prepared reviews.
  """
  prepared_reviews = []
  for review in reviews:
    review_title = review.get("title")
    review_text = review.get("text")
    review_id = review.get("timestamp")
    if review_title and review_text:
      if len(review_text.split()) > max_review_words:
        continue
      prepared_reviews.append({"review_id":review_id, "title":review_title, "text":review_text})
  return prepared_reviews


def aggregate_by_attribute(
    review_outputs: List[ReviewResult],
    *,
    count_mixed_as: str = "both",  # "both" | "neither" | "positive" | "negative"
) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate per-attribute stats from a list of ReviewResult (Pydantic models).

    Returns:
      {
        "<attribute>": {
          "mention_count": int,
          "positive_count": int,
          "negative_count": int,
          "reviews": [
            {
              "review_id": str,
              "sentiment": str,
              "evidence": str,
              "confidence": float
            },
            ...
          ]
        },
        ...
      }
    """
    if count_mixed_as not in {"both", "neither", "positive", "negative"}:
        raise ValueError("count_mixed_as must be one of: 'both', 'neither', 'positive', 'negative'")

    out: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"mention_count": 0, "positive_count": 0, "negative_count": 0, "neutral_count":0, "reviews": []}
    )

    for review in review_outputs:
        review_id = review.review_id

        for ar in (review.attributes or []):
            attr = ar.attribute
            if not attr:
                continue

            sentiment = (ar.sentiment or "not_mentioned").strip().lower()
            evidence = ar.evidence or ""
            confidence = float(ar.confidence) if ar.confidence is not None else None
            # Mention count + per-review details
            if sentiment != "neutral":
              out[attr]["mention_count"] += 1
              out[attr]["reviews"].append(
                  {
                      "review_id": review_id,
                      "sentiment": sentiment,
                      "evidence": evidence,
                      "confidence": confidence,
                  }
              )

            # Sentiment counts
            if sentiment == "positive":
                out[attr]["positive_count"] += 1
            elif sentiment == "negative":
                out[attr]["negative_count"] += 1
            elif sentiment == "mixed":
                if count_mixed_as == "both":
                    out[attr]["positive_count"] += 1
                    out[attr]["negative_count"] += 1
                elif count_mixed_as == "positive":
                    out[attr]["positive_count"] += 1
                elif count_mixed_as == "negative":
                    out[attr]["negative_count"] += 1

    return dict(out)

def aggregation_to_dfs(
    agg: Dict[str, Dict[str, Any]],
    reviews_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Convert aggregate_by_attribute() output into:
      1) summary_df: one row per attribute with counts
      2) details_df: one row per (attribute, review_id) with sentiment/evidence/confidence
    """
    summary_rows = []
    detail_rows = []

    def enrich_details_with_reviews(
    details_df: pd.DataFrame,
    reviews_df: pd.DataFrame,
) -> pd.DataFrame:
      """
      Add full review text + metadata to details_df.
      """
      enriched_df = details_df.merge(
          reviews_df,
          on="review_id",
          how="left",
          validate="many_to_one",  # many attributes per review → one review row
      )

      return enriched_df

    for attribute, stats in agg.items():
        if stats.get("positive_count") == 0 and stats.get("negative_count") == 0:
            continue
        summary_rows.append({
            "attribute": attribute,
            "mention_count": stats.get("mention_count", 0),
            "positive_count": stats.get("positive_count", 0),
            "negative_count": stats.get("negative_count", 0),
        })

        for r in stats.get("reviews", []):
            detail_rows.append({
                "attribute": attribute,
                "review_id": r.get("review_id"),
                "sentiment": r.get("sentiment"),
                "evidence": r.get("evidence"),
                "confidence": r.get("confidence"),
            })

    summary_df = pd.DataFrame(summary_rows).sort_values("mention_count", ascending=False).reset_index(drop=True)
    details_df = pd.DataFrame(detail_rows).reset_index(drop=True)
    details_df = enrich_details_with_reviews(details_df, reviews_df)
    return summary_df, details_df


def return_none_on_failure(retry_state):
    # called when retries are exhausted
    return None