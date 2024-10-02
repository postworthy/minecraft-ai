import argparse
import os
import uuid
import torch
import json
from datasets import Dataset
from trl import SFTTrainer
from datasets import load_dataset
from transformers import TrainingArguments, TextStreamer
from unsloth.chat_templates import get_chat_template
from unsloth import FastLanguageModel, is_bfloat16_supported
from util import load_models, get_dataset_idx_by_function_name, get_unique_function
from create_dataset import create_dataset
from datasets import concatenate_datasets
from eval import run_eval

max_seq_length = 2048

def apply_function_filter(dataset, limit=0):
    functions = list(get_unique_function(dataset).keys())
    function_filters = []
    
    if limit == 0:
        limit == 100

    for function_name in functions:
        if function_name == "move":
            function_filters.append((function_name, limit*.2, "left"))
            function_filters.append((function_name, limit*.2, "right"))
            function_filters.append((function_name, limit, "forward"))
            function_filters.append((function_name, limit*.2, "backward"))
        else:
            function_filters.append((function_name, limit, None))

    filtered_dataset_idx = []
    for function_filter in function_filters:
        print(f"Filtering function {function_filter[0]} with limit={function_filter[1]}")

        function_dataset_idx = list(get_dataset_idx_by_function_name(dataset, function_filter[0], function_filter[1], function_filter[2]))
        if len(function_dataset_idx) > 0:
            print(f"{len(function_dataset_idx)} items selected for {function_filter[0]}")
            filtered_dataset_idx.extend(function_dataset_idx)
        else:
            print(f"{len(function_dataset_idx)} items selected for {function_filter[0]}")

    return dataset.select(filtered_dataset_idx)

def get_dataset(dataset_dir, function_filter_limit):
    if os.path.exists(dataset_dir):
        print(f"Dataset already exists at {dataset_dir}. Loading dataset...")
        dataset = Dataset.load_from_disk(dataset_dir)
        print("Dataset loaded successfully.")
    else:
        raise Exception(f"No dataset found at {dataset_dir}")


    if function_filter_limit > 0:
        print(f"Applying function filter to dataset ({function_filter_limit}).")
        dataset = apply_function_filter(dataset, function_filter_limit)

    print("First few rows in dataset:")
    for idx in range(min(5, len(dataset))):
        example = dataset[idx]
        print(f"Example {idx}: Type={type(example)}, Content={example}")
        if 'text' not in example:
            print(f"Error: Example {idx} is missing 'text' key.")
        elif not isinstance(example['text'], str):
            print(f"Error: 'text' in Example {idx} is not a string.")

    return dataset

def main():
    parser = argparse.ArgumentParser(description='LLM training')
    parser.add_argument('--input-dir', type=str, default="./input", help='Path to the input directory containing JSON files.')
    parser.add_argument('--output-dir', type=str, default="./output", help='Path to the output directory to save combined files.')
    parser.add_argument('--checkpoint-path', type=str, default=None, help='Path to a model checkpoint to load.')
    parser.add_argument('--dataset-name', type=str, default="dataset", help='Prefix to LLM training prompt.')
    parser.add_argument('--apply-function-filter', type=int, default=0, help='Filter functions to N occurences.')
    parser.add_argument('--epochs', type=int, default=1, help='Training Epochs.')

    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir
    dataset_name = args.dataset_name
    dataset_dir = os.path.join(output_dir, dataset_name)
    checkpoint_path = args.checkpoint_path
    function_filter_limit = args.apply_function_filter
    epochs = args.epochs

    model, tokenizer = load_models(checkpoint_path)

    run_id = str(uuid.uuid4())

    print(f"Training (run id:{run_id})...")

    final_train_loss = 0.0

    for i in range(epochs):
        print(f"Training epoch {i+1}")
        checkpoint_dir = f"{output_dir}/checkpoints-{dataset_name}-{run_id}-{i}"
        os.makedirs(checkpoint_dir, exist_ok=True)
        current_dataset = get_dataset(dataset_dir, function_filter_limit)
        trainer=SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            train_dataset=current_dataset,
            dataset_text_field="text",
            max_seq_length=max_seq_length,
            dataset_num_proc=2,
            packing=True,
            args=TrainingArguments(
                learning_rate=3e-4,
                lr_scheduler_type="linear",
                per_device_train_batch_size=8,
                gradient_accumulation_steps=2,
                num_train_epochs=1,
                fp16=not is_bfloat16_supported(),
                bf16=is_bfloat16_supported(),
                logging_steps=1,
                optim="adamw_8bit",
                weight_decay=0.01,
                warmup_steps=10,
                output_dir=checkpoint_dir,
                seed=0,
            ),
        )

        if i == 0 and checkpoint_path:
            training_output = trainer.train(resume_from_checkpoint=checkpoint_path)
        else:
            training_output = trainer.train()

        train_loss = training_output.metrics.get('train_loss')
        if train_loss is not None:
            final_train_loss = train_loss
        else:
            print(f"Warning: 'train_loss' not found in metrics for epoch {i+1}")

    
        print(f"Running eval after epoch {i+1}...")
        run_eval(model, tokenizer, current_dataset)


    model_dir = os.path.join(output_dir, f'model-for-{dataset_name}-{run_id}-loss-{final_train_loss:.4f}-max-seq-{max_seq_length}')
    print(f"Saving model to {model_dir}...")
    model.save_pretrained_merged(model_dir, tokenizer, save_method="merged_16bit")

    print("Running Final Eval...")
    run_eval(model, tokenizer, Dataset.load_from_disk(dataset_dir))

if __name__ == "__main__":
    main()