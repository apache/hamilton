#!/bin/bash
# attribute variables
target_dir=$1
api_key=$2

# Step 1: Clone the repository
if [ -d "$target_dir" ]; then
    echo "The target directory '$target_dir' already exists."

    # Optionally, prompt the user for confirmation
    read -p "Do you want to overwrite it? (y/n): " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # Remove the existing directory and then perform the git clone
        rm -rf "$target_dir"
        git clone https://github.com/apache/hamilton.git "$target_dir/hamilton"
    else
        echo "Clone operation canceled."
    fi
else
    # If the target directory doesn't exist, perform the git clone
    git clone https://github.com/apache/hamilton.git "$target_dir/hamilton"
fi

# # Step 2: Move to the directory
cd "$target_dir/hamilton/examples/LLM_Workflows/retrieval_augmented_generation"

# Step 3: Create an .env file with your OpenAI API key
if [ $# -ne 2 ]; then
  echo "Please provide your OpenAI API key as an argument."
  exit 1
fi

touch .env
echo "OPENAI_API_KEY=$api_key" >> .env

# Step 5: Create docker containers
docker compose up -d --build

# Step 6: Wait for containers to start and display URLs
echo "Waiting for containers to start..."
sleep 10 # You can adjust this sleep duration as needed
echo "Streamlit app is running at http://localhost:8080/"
echo "FastAPI documentation is available at http://localhost:8082/docs"
echo "Weaviate documentation is available at http://localhost:8083/v1"
