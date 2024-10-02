import requests
import os
import argparse
from util import extract_timestamp
import subprocess
import re

# Define the function to call Ollama
def call_ollama(model, prompt):
    url = f"{os.getenv('OLLAMA_URL')}api/generate"
    payload = {
        "stream": False,
        "model": model,
        "prompt": prompt
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            response_data = response.json()
            print(f"Generated response for model '{model}':", response_data.get("response", "No text generated"))
            return response_data.get("response", "ERROR")
        else:
            print(f"Failed to generate response. Status code: {response.status_code}, Response: {response.text}")
            return "ERROR"
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return "ERROR"

def get_action_yaml(text):
    # Use regex to find the last occurrence of "action:" at the start of a line
    match = list(re.finditer(r'^action:', text, re.MULTILINE))
    
    if match:
        # Get the last match
        last_action_index = match[-1].start()
        human_value = text[:last_action_index]
        gpt_value = text[last_action_index:]
        
        return f"\n\nGiven my analysis above the next predicted action would be:\n\n```yml\n{gpt_value}\n```"
    else:
        raise Exception("action section not found")

def get_files_with_keyword(input_dir, keyword):
    print(f"Using `grep` to filter input files based on keyword: `{keyword}`")
    try:
        # Use grep to search for files containing the keyword and list only file names
        result = subprocess.run(
            ['grep', '-rl', keyword, input_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Check if grep found any matches
        if result.returncode == 0:
            # The result will contain the list of files (one per line) that match the keyword
            files = result.stdout.splitlines()
            return files
        else:
            # No files found or an error occurred
            print(f"No files found containing the keyword '{keyword}'.")
            return []
    except Exception as e:
        print(f"An error occurred during grep execution: {e}")
        return []



def process_files(model, input_dir, output_dir, keyword=None):    
    # Get all the .yaml files in the input directory
    files = [f for f in os.listdir(input_dir) if f.endswith('.yaml')]
    # Sort the files based on their extracted timestamp
    sorted_files = sorted(files, key=lambda f: extract_timestamp(f))

    if len(sorted_files) < 2:
        raise Exception("You must have at least 2 files to process in this way.")

    if keyword:
        filtered_files = get_files_with_keyword(input_dir, keyword)
        sorted_filtered_files = sorted(filtered_files, key=lambda f: extract_timestamp(f))
        if len(sorted_filtered_files) < 2:
            raise Exception(f"You must have at least 2 files to process in this way. (keyword:{keyword})")

    files_to_process = sorted_filtered_files if keyword else sorted_files

    for i in range(len(files_to_process)-1):
        filename = os.path.basename(files_to_process[i])
        next_filename = sorted_files[sorted_files.index(filename) + 1]
        file_path = os.path.join(input_dir, filename)
        next_file_path = os.path.join(input_dir, next_filename)
        with open(file_path, 'r') as file:
            with open(next_file_path, 'r') as next_file:
                data = file.read()
                next_data = next_file.read()
                # Create output file name based on input file name
                base_filename = os.path.splitext(filename)[0]
                output_filename = f"{base_filename}-llama.txt"
                output_path = os.path.join(output_dir, output_filename)

                prompt = f"Act as an expert Minecraft player who can understand a player's actions by viewing the game state at the time the action was given. I will provide you with the game state and the action taken in YAML form, and you will tell me why a player may have taken the given action using your knowledge of Minecraft and the game state, be highly detailed and provide your reasoning step by step for the sample data below:\n\n{data}\n\n"

                if os.path.exists(output_path):
                    print(f"Output file {output_filename} already exists. Skipping...")
                    with open(output_path, 'r') as output_file:
                        existing_response = output_file.read()
                        yield (prompt, existing_response + get_action_yaml(next_data))
                    continue
                
                
                response = call_ollama(model, prompt)
                
                # Save the response to the output file
                with open(output_path, 'w') as output_file:
                    output_file.write(response)
                    print(f"Response saved to {output_path}")

                yield (prompt, response + get_action_yaml(next_data))

def main():
    parser = argparse.ArgumentParser(description='LLM training')
    parser.add_argument('--input-dir', type=str, default="./input", help='Path to the input directory containing YAML files.')
    parser.add_argument('--output-dir', type=str, default="./output/llama", help='Path to the output directory to save the generated responses.')
    parser.add_argument('--model', type=str, default="llama3.1", help='Ollama model name')
    parser.add_argument('--keyword', type=str, default=None, help='Keyword to filter files by content')
   
    args = parser.parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir
    model = args.model
    keyword = args.keyword

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    process_files(model, input_dir, output_dir, keyword)

if __name__ == "__main__":
    main()
