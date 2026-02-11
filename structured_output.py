from pydantic import BaseModel, Field, ValidationError
from typing import List


class AttributeResult(BaseModel):
  attribute: str = Field(description="Attribute of a product.")
  match_type: str = Field(description="Wether attribute already exists or ie newly created.")
  # match_confidence: float = Field(description="Confidence in matching attribute between 0 and 1.")
  # mentioned: bool = Field(description="Whether the attribute is mentioned or clearly implied.")
  sentiment: str = Field(description="The sentiment toward that attribute: positive, negative, mixed.")
  evidence: str = Field(description="A short evidence quote copied verbatim from the review that supports your decision.")
  confidence: float = Field(description="confidence between 0 and 1")

class ReviewResult(BaseModel):
  review_id: str = Field(description="Review ID.")
  attributes: List[AttributeResult] = Field(description="List of attribute results.")