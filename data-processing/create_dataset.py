import argparse
import os
import torch
import json
from datasets import Dataset
from util import load_models, apply_template
from sliding_window import process_files as process_files_sw
from llama_data_pre_processing import process_files as process_files_llama

DEFAULT_PRE="Below I have provided a short history of minecraft game data and player actions, act as an expert minecraft player and suggest the next appropriate action to be taken next based on the game data provided.\n\n"

functions = [
                ("function: move",            5000),
                ("function: interact_block",  1000),
                ("function: player_sleep",    1000),
                ("function: use_item",        1000),
                ("function: pickup_item",     1000),
                ("function: attack_entity",   1000),
                ("function: container_event", 1000),
                ("function: player_wake",     1000),
                ("function: destroy_item",    1000),
                ("function: craft_item",      1000),
             ]

def create_dataset_llama(tokenizer, input_dir, output_dir, dataset_dir, model="llama3.1"):
    if not os.path.isdir(input_dir):
        print(f"Error: The directory '{input_dir}' does not exist.")
        return
    
    messages = []

    print(f"Processing Data via Ollama w/ {model}...")

    for f, max in functions:
        i = 0
        for human, gpt in process_files_llama(model, input_dir, output_dir, f):        
            data = [
                {
                    "from": "human",
                    "value": human.strip()
                },
                {
                    "from": "gpt",
                    "value": gpt.strip()
                }
            ]
            messages.append([data])
            i += 1
            if i >= max:
                break

    print(f"Number of messages loaded: {len(messages)}")
    for idx, message in enumerate(messages[:5]):
        print(f"Message {idx}: Type={type(message)}, Content={message}")


    print(f"Applying Template...")

    dataset_list = apply_template(tokenizer, messages)
    dataset = Dataset.from_list(dataset_list)

    dataset.save_to_disk(dataset_dir)

    print(f"Data saved to {dataset_dir}")

    return dataset

def create_dataset(tokenizer, input_dir, dataset_dir, sliding_window_size=3, pre=DEFAULT_PRE):
    if not os.path.isdir(input_dir):
        print(f"Error: The directory '{input_dir}' does not exist.")
        return
    
    messages = []

    print(f"Loading Data...")

    for text in process_files_sw(input_dir, sliding_window_size, True):        
        last_action_index = text.rfind('action:')
        human_value = text[:last_action_index]
        gpt_value = text[last_action_index:]
        data = [
            {
                "from": "human",
                "value": pre + human_value.strip()
            },
            {
                "from": "gpt",
                "value": gpt_value.strip()
            }
        ]
        messages.append([data])

    print(f"Number of messages loaded: {len(messages)}")
    for idx, message in enumerate(messages[:5]):
        print(f"Message {idx}: Type={type(message)}, Content={message}")


    print(f"Applying Template...")

    dataset_list = apply_template(tokenizer, messages)
    dataset = Dataset.from_list(dataset_list)

    dataset.save_to_disk(dataset_dir)

    print(f"Data saved to {dataset_dir}")

    return dataset


def create_dataset_old(tokenizer, input_dir, dataset_dir):
    if not os.path.isdir(input_dir):
        print(f"Error: The directory '{input_dir}' does not exist.")
        return

    json_files = [
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.endswith(('.json'))
    ]

    if not json_files:
        print(f"No JSON files found in directory '{input_dir}'.")
        return

    messages = []

    print(f"Loading Data...")

    for file_path in json_files:
        with open(file_path, 'r') as f:
            data = json.load(f)

            messages.append([data])

    print(f"Number of messages loaded: {len(messages)}")
    for idx, message in enumerate(messages[:5]):
        print(f"Message {idx}: Type={type(message)}, Content={message}")


    print(f"Applying Template...")

    dataset_list = apply_template(tokenizer, messages)
    dataset = Dataset.from_list(dataset_list)

    dataset.save_to_disk(dataset_dir)

    print(f"Data saved to {dataset_dir}")

    return dataset

def main():
    parser = argparse.ArgumentParser(description='LLM training')
    parser.add_argument('--input-dir', type=str, default="./input", help='Path to the input directory containing JSON files.')
    parser.add_argument('--output-dir', type=str, default="./output", help='Path to the output directory to save combined files.')
    parser.add_argument('--sliding-window-size', type=int, default=3, help='Size of the sliding window.')
    parser.add_argument('--pre-prompt', type=str, default=None, help='Prefix to LLM training prompt.')
    parser.add_argument('--use-llama', action='store_true', help='Process data with llama via ollama')
    parser.add_argument('--dataset-name', type=str, default="dataset", help='Name of the dataset.')

    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir
    dataset_name = args.dataset_name
    dataset_dir = os.path.join(output_dir, dataset_name)
    sliding_window_size = args.sliding_window_size
    pre = args.pre_prompt
    use_llama = args.use_llama

    model, tokenizer = load_models()

    if use_llama:
        create_dataset_llama(tokenizer, input_dir, './output/llama', dataset_dir)
    elif pre == None:
        create_dataset(tokenizer, input_dir, dataset_dir, sliding_window_size)
    else:
        create_dataset(tokenizer, input_dir, dataset_dir, sliding_window_size, pre)

if __name__ == "__main__":
    main()