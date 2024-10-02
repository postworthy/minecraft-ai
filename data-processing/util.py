import os
from unsloth.chat_templates import get_chat_template
from unsloth import FastLanguageModel
import random
import re
from datetime import datetime

max_seq_length = 2048

# Define a function to extract the timestamp from the filename
def extract_timestamp(filename):
    # Regex to match the timestamp in the filename
    match = re.search(r'data_(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.\d+)\.yaml', filename)
    if match:
        timestamp_str = match.group(1)
        # Split the timestamp into the datetime part and microseconds
        dt_part, microseconds = timestamp_str.split('.')
        # Truncate microseconds to 6 digits if it's longer
        microseconds = microseconds[:6]
        # Reconstruct the timestamp string with the truncated microseconds
        truncated_timestamp_str = f"{dt_part}.{microseconds}"
        # Convert the string to a datetime object
        return datetime.strptime(truncated_timestamp_str, '%Y-%m-%dT%H-%M-%S.%f')
    return None

def apply_template(tokenizer, messages):
    texts = [tokenizer.apply_chat_template(message, tokenize=False, add_generation_prompt=False) for message in messages]
    return [{'text': t[0]} for t in texts]

def load_models(checkpoint_path=None):
    if checkpoint_path and os.path.exists(checkpoint_path):
        print(f"Loading model from checkpoint at {checkpoint_path}...")

        model, tokenizer = FastLanguageModel.from_pretrained(
            checkpoint_path,
            max_seq_length=max_seq_length,
            load_in_4bit=True,
            dtype=None,
        )
    else:
        if checkpoint_path:
            print(f"Checkpoint does not exist at ({checkpoint_path}). Initializing model from pre-trained weights.")
        else:
            print("No valid checkpoint provided. Initializing model from pre-trained weights.")

        model, tokenizer = FastLanguageModel.from_pretrained(
            #model_name="unsloth/Meta-Llama-3.1-8B-bnb-4bit",
            #model_name="unsloth/Llama-3.2-3B-bnb-4bit",
            model_name="unsloth/Llama-3.2-1B-Instruct-bnb-4bit",
            max_seq_length=max_seq_length,
            load_in_4bit=True,
            dtype=None,
        )

    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        lora_alpha=16,
        lora_dropout=0,
        target_modules=["q_proj", "k_proj", "v_proj", "up_proj", "down_proj", "o_proj", "gate_proj"], 
        use_rslora=True,
        use_gradient_checkpointing="unsloth"
    )

    tokenizer = get_chat_template(
        tokenizer,
        mapping={"role": "from", "content": "value", "user": "human", "assistant": "gpt"},
        chat_template="chatml",
    )

    return model, tokenizer

def get_unique_function(dataset):
    unique_functions = {}
    for idx in range(len(dataset)):
        example = dataset[idx]
        input_text = example['text']

        # Split the input_text to separate the prompt and the assistant's response
        assistant_token = '<|im_start|>assistant'
        if assistant_token in input_text:
            prompt_text, rest = input_text.split(assistant_token)
            prompt_text += assistant_token  # Include the assistant token at the end
            assistant_text = rest.strip()
            # Remove any trailing <|im_end|> token if present
            if '<|im_end|>' in assistant_text:
                assistant_text = assistant_text.split('<|im_end|>')[0].strip()
        else:
            # If the assistant token is not found, skip this example
            continue

        # Check if 'function: ' is in the assistant's text
        if 'function: ' in assistant_text:
            # Extract the function name
            # Assuming the function name follows 'function: ' and is up to the next newline or period
            _, _, rest = assistant_text.rpartition("function: ")
            function_name = rest.split('\n')[0].split('.')[0].strip()

            # If we haven't already collected an example for this function, add it
            if function_name not in unique_functions:
                unique_functions[function_name] = {
                    'index': idx,
                    'prompt_text': prompt_text,
                    'assistant_text': assistant_text,
                    'example': example
                }
    
    return unique_functions

def get_dataset_idx_by_function_name(dataset, function_name, limit=0, filter=None):
    matches=0
    indices = list(range(len(dataset)))
    random.shuffle(indices)

    for idx in indices:
        example = dataset[idx]
        input_text = example['text']
        assistant_token = '<|im_start|>assistant'
        if assistant_token in input_text:
            _, rest = input_text.split(assistant_token)
            if "function: " in rest:
                _, _, rest = rest.rpartition("function: ")
                if function_name in rest:
                    if filter == None or filter in rest:
                        matches += 1
                        yield idx
            
            if limit > 0 and matches >= limit:
                return