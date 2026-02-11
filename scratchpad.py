import pandas as pd
from collections import defaultdict
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





def clean_attributes(product, attribute_list):
  #formatted_attributes = "\n".join([str(attribute) for attribute in aggregated_results.keys]

  #attributes = """battery_life price brightness led_light case_quality durability usability waterproofing battery weight battery_type power water_resistance battery_connection emergency_preparedness reliability"""
#   attributes = '''
# usability
# compatibility
# economy
# prev_product_experience
# price
# delivery
# prev_usability
# material
# '''
  
  
  formatted_attributes = "\n".join(attribute_list)
  clean_attributes_prompt = """You are an expert in product attribute taxonomy design.

You will be given:
- A product name
- A list of extracted attribute names (may contain redundancy, noise, or low-quality attributes).

Task:
Produce a cleaned, consolidated list of PRODUCT attributes.

STEP 1 — Validate attributes:
- Remove attributes that do NOT present any meaningful value to a customer reading the reviews.

STEP 2 — Combine similar attributes:
- Group attributes that refer to the same underlying product concept.
- Create ONE canonical attribute name per group.
- Canonical names must be:
  - concise (1–3 words)
  - standardized
  - lowercase
  - user-meaningful (what a buyer would care about)

STEP 3 — Output:
For each final attribute:
- Provide the canonical attribute name
- List ALL original attributes that were combined into it
- If an attribute was discarded, list it separately with a short reason

IMPORTANT:
- Do NOT invent new attributes beyond consolidation.
- Do NOT lose information when merging (all merged attributes must be listed).
- If an attribute cannot be reasonably merged and is valid, keep it as-is.

Product:
{PRODUCT_NAME}

Extracted attributes:
{ATTRIBUTE_LIST}

Return ONLY valid JSON in the following schema:
{{
  "final_attributes": [
    {{
      "attribute": "<canonical attribute name>",
      "combined_from": ["<original attribute>", "..."]
    }}
  ],
  "discarded_attributes": [
    {{
      "attribute": "<original attribute>",
      "reason": "<short reason>"
    }}
  ]
}}

  """

  llm = ChatHuggingFace(
      llm=HuggingFaceEndpoint(
          repo_id="mistralai/Mistral-7B-Instruct-v0.2",
          temperature=0,
      )
  )
  prompt = ChatPromptTemplate.from_template(clean_attributes_prompt)
  chain = (
      prompt
      | llm
  )

  result = chain.invoke({
    "ATTRIBUTE_LIST": formatted_attributes,
    "PRODUCT_NAME":product
  })

  #print(result.messages[0].content)
  print(result.content)



attribute_summary = pd.read_csv("/home/divyam/Documents/Learning/Product Review summarizer/Results/Tools_and_Home_Improvement/Tools_and_Home_Improvement_summary_25.csv")
attribute_details = pd.read_csv("/home/divyam/Documents/Learning/Product Review summarizer/Results/Tools_and_Home_Improvement/Tools_and_Home_Improvement_details_25.csv")


# ls = []

# for i, row in enumerate(attribute_summary.iterrows()):
#   dic = {}
#   dic["attribute_name"] = row[1]["attribute"]
#   dic["evidence_examples"] = list(attribute_details[attribute_details["attribute"] == row[1]["attribute"]]["evidence"])

# #   print(dic)
#   ls.append(dic)

attribute_list = list(attribute_summary["attribute"])
product = "RAYOVAC Floating LED Lantern Flashlight, 6V Battery Included, Superb Battery Life, Floats for Easy Water Recovery, Emergency Light"
clean_attributes(product, attribute_list)
