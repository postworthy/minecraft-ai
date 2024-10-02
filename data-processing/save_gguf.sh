#!/bin/bash

# Usage:
#   ./convert_models.sh [output_directory]
#
# If no output_directory is provided, it defaults to "./output"

# Set the output directory (default to "./output" if not provided)
OUTPUT_DIR="${1:-./output}"

# Path to the Python conversion script
CONVERT_SCRIPT="llama.cpp/convert_hf_to_gguf.py"

# Check if the conversion script exists
if [ ! -f "$CONVERT_SCRIPT" ]; then
    echo "Error: Conversion script '$CONVERT_SCRIPT' not found."
    exit 1
fi

# Define the types and their corresponding outtype values
declare -A TYPE_OUTTYPE_MAP=(
    ["f16"]="f16"
    #["bf16"]="bf16"
    ["q8_0"]="q8_0"
)

# Iterate over each model-* directory in the output directory
for MODEL_DIR in "$OUTPUT_DIR"/model-*; do
    if [[ ! $MODEL_DIR == *gguf ]]; then
        # Ensure it's a directory
        if [ -d "$MODEL_DIR" ]; then
            # Extract the base model name (e.g., model-for-dataset-sw2-f902fa17-702b-4d67-9e14-83ee61a0ccfa-loss-0.0144)
            MODEL_NAME=$(basename "$MODEL_DIR")
            
            # Define the corresponding gguf directory
            GGUF_DIR="${OUTPUT_DIR}/${MODEL_NAME}-gguf"
            
            # Create the gguf directory if it doesn't exist
            if [ ! -d "$GGUF_DIR" ]; then
                echo "GGUF directory '$GGUF_DIR' does not exist. Creating it."
                mkdir -p "$GGUF_DIR"
                if [ $? -ne 0 ]; then
                    echo "Error: Failed to create directory '$GGUF_DIR'. Skipping '$MODEL_NAME'."
                    continue
                fi
            fi
            
            # Iterate over each type (fp16, int8, int4)
            for TYPE in "${!TYPE_OUTTYPE_MAP[@]}"; do
                OUTTYPE="${TYPE_OUTTYPE_MAP[$TYPE]}"
                
                # Define the expected output binary file
                OUTFILE="${GGUF_DIR}/${MODEL_NAME}-gguf.${TYPE}.gguf"
                
                # Check if the output file already exists
                if [ -f "$OUTFILE" ]; then
                    echo "[$TYPE] Binary already exists for '$MODEL_NAME' at '$OUTFILE'. Skipping conversion."
                    continue
                fi
                
                echo "[$TYPE] Starting conversion for '$MODEL_NAME'..."
                
                # Perform the conversion
                python3 "$CONVERT_SCRIPT" "$MODEL_DIR/" \
                    --outtype "$OUTTYPE" \
                    --outfile "$OUTFILE"
                
                # Check if the conversion was successful
                if [ $? -eq 0 ]; then
                    echo "[$TYPE] Conversion successful for '$MODEL_NAME'. Output saved to '$OUTFILE'."
                else
                    echo "[$TYPE] Error: Conversion failed for '$MODEL_NAME'."
                fi
            done
        else
            echo "Skipping '$MODEL_DIR' as it is not a directory."
        fi
    fi
done

echo "All eligible models have been processed."
