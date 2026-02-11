# Design Document: Product Review Summarizer

## Problem Statement
E-commerce platforms generate vast amounts of user-generated content in the form of product reviews. For popular products, the volume of reviews can be overwhelming for potential customers to parse. Key information—such as specific feedback on "battery life," "comfort," or "sizing"—is often buried within long, unstructured text.

Customers need a way to quickly understand the consensus on specific product attributes without reading hundreds of individual reviews. The goal of this project is to build an automated **Aspect-Based Sentiment Analysis (ABSA)** system that can:
1.  **Extract features/attributes** (e.g., "screen quality", "price", "durability") from unstructured review text.
2.  **Determine sentiment** (Positive, Negative, Mixed) associated with each specific attribute.
3.  **Provide evidence** by extracting verbatim quotes from the reviews.
4.  **Aggregate results** to provide a high-level summary of product performance across different dimensions.

## Approach

The solution leverages Large Language Models (LLMs) to perform zero-shot extraction and sentiment analysis, enforced with structured output validation.

### 1. Data Ingestion & Preparation
*   **Source**: The system uses the `McAuley-Lab/Amazon-Reviews-2023` dataset from Hugging Face, specifically targeting the "Clothing_Shoes_and_Jewelry" category (configurable).
*   **Filtering**: It identifies a specific product with a sufficient number of reviews.
*   **Preprocessing**: Reviews are filtered to remove excessive length (>100 words by default) to ensure they fit within the context window and focus on concise feedback.

### 2. Core Logic: LLM-Based Extraction
*   **Model**: The system uses `mistralai/Mistral-7B-Instruct-v0.2` via the HuggingFace Inference Endpoint.
*   **Prompting Strategy**:
    *   Use of a specialized prompt (`prompts.identify_attributes_prompt`) that instructs the model to act as an expert in aspect-based sentiment analysis.
    *   **Iterative Attribute Discovery**: The system maintains a running list of "canonical attributes" found in previous reviews. This list is passed to the LLM for subsequent reviews to encourage normalization (e.g., mapping "the fit" and "fitting" to a single attribute like "fit").
    *   **Sentiment & Evidence**: The model is required to output a sentiment classification and a direct quote for every identified attribute.

### 3. Structured Output & Robustness
*   **Schema Enforcement**: Output is strictly defined using **Pydantic** models (`ReviewResult`, `AttributeResult`) to ensure consistency.
    *   Fields include: `attribute`, `match_type`, `sentiment`, `evidence`, and `confidence`.
*   **Error Handling**: The system utilizes the `tenacity` library to retry LLM calls if the output fails validation (e.g., malformed JSON). This ensures high reliability in the processing pipeline.

### 4. Aggregation of Results
*   **Post-Processing**: Individual review results are aggregated to calculate:
    *   **Mention Count**: How often an attribute is discussed.
    *   **Sentiment Distribution**: Counts of positive vs. negative mentions.
*   **Output Generation**:
    *   `summary_{name}.csv`: High-level statistics for each attribute.
    *   `details_{name}.csv`: A comprehensive log of every mention, including the source review ID, specific evidence quote, and confidence score, allowing for deep-diving into the data.
