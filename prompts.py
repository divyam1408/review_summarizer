

identify_attributes_prompt = '''You are an expert in aspect-based sentiment analysis and attribute normalization.

You will be given:
1) A product name
2) A product review
3) A list of existing canonical attribute names (a controlled vocabulary).

Task:
Generate a list of product attributes/aspects which the review talks about, helping future customers to make informed decisions.

STEP 1 - Identify Attributes:
- Identify which relevant attributes/aspects the review talks about.
- For every identified attribute/aspect, see if it is similar to any of the existing attributes from the given list of canonical attributes.
- If it is similar to any existing attribute, you MUST use the existing canonical attribute name EXACTLY as provided (character-for-character).
- If it is NOT similar to any existing attribute, create a new attribute/aspect, which should be concise (1–3 words), standardized, lowercase and customer friendly.


STEP-2 - For EACH final attribute provide the following:
- sentiment: one of ["positive","negative","mixed"] showcasing sentiment of the review towards the attribute/aspect.
- evidence: a short verbatim quote from the review supporting the sentiment.
- confidence: 0–1 for sentiment confidence.

Additional rules:
- If praise exists for the attribute/aspect, sentiment must be "positive".
- If complaint exists for the attribute/aspect, sentiment must be "negative".
- If both praise and complaint exist for the attribute/aspect, use "mixed".
- Do NOT infer sentiment without textual evidence.
- Output JSON only (no markdown, no extra text.
- DO NOT WRAP THE OUTPUT JSON IN ```json or ```

Below are the details to answer the query

Product Name:
{PRODUCT_NAME}

Existing canonical attributes:
{EXISTING_ATTRIBUTES_LIST}

Review:
{REVIEW_TEXT}


Return only the JSON in following schema:
{{
"review_id": "<string>",
"attributes": [
{{
    "attribute": "<exact existing attribute name OR new attribute name>",
    "match_type": "<existing | new>",
    "sentiment": "<positive | negative | mixed>",
    "evidence": "<verbatim quote>",
    "confidence": <number between 0 and 1>
}}
]
}}

'''