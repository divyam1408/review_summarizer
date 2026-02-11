#!/bin/bash

# Default values
DEFAULT_CATEGORY="Clothing_Shoes_and_Jewelry"
DEFAULT_NUM_REVIEWS=5
DEFAULT_OUTPUT_NAME="experiment_results"

# Prompt for Product Category
read -p "Enter Product Category [${DEFAULT_CATEGORY}]: " category
category=${category:-$DEFAULT_CATEGORY}

# Prompt for Number of Reviews
read -p "Enter Number of Reviews to Classify [${DEFAULT_NUM_REVIEWS}]: " num_reviews
num_reviews=${num_reviews:-$DEFAULT_NUM_REVIEWS}

# Prompt for Output Name
read -p "Enter Output Name [${DEFAULT_OUTPUT_NAME}]: " output_name
output_name=${output_name:-$DEFAULT_OUTPUT_NAME}

echo "Running summarizer with:"
echo "Category: $category"
echo "Number of Reviews: $num_reviews"
echo "Output Name: $output_name"

python3 summarize_reviews.py --category "$category" --num_reviews "$num_reviews" --output_name "$output_name"
