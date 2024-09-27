import argparse
import os
import random
import torch
from datasets import Dataset
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
from util import get_unique_function

def run_eval(model, tokenizer, dataset):
    unique_functions = get_unique_function(dataset)
    num_functions_to_sample = min(10, len(unique_functions))
    sampled_functions = random.sample(list(unique_functions.keys()), num_functions_to_sample)


    print("Starting evaluation on randomly sampled data...\n")

    for function_name in sampled_functions:
        # Get the dataset example
        data = unique_functions[function_name]
        idx = data['index']
        prompt_text = data['prompt_text']
        expected_response = data['assistant_text']

        # Tokenize the prompt_text
        inputs = tokenizer(
            prompt_text,
            return_tensors="pt",
            add_special_tokens=False
        )

        # Generate the model's response
        FastLanguageModel.for_inference(model)
        with torch.no_grad():
            outputs = model.generate(
                input_ids=inputs['input_ids'],
                attention_mask=inputs['attention_mask'],
                max_new_tokens=200,
                do_sample=True,
                top_p=0.95,
                temperature=0.8,
                eos_token_id=tokenizer.eos_token_id,
            )
        FastLanguageModel.for_training(model)

        # Decode the generated response
        generated_tokens = outputs[0][inputs['input_ids'].shape[1]:]
        generated_text = tokenizer.decode(generated_tokens, skip_special_tokens=True)

        # Display the results
        print(f"--- Sample {idx} ---")
        print("Input Prompt:")
        print(prompt_text)
        print("\nExpected Response:")
        print(expected_response.strip())
        print("\nModel's Generated Response:")
        print(generated_text.strip())
        print("\n" + "="*50 + "\n")


def main():
    parser = argparse.ArgumentParser(description='LLM Eval')
    parser.add_argument('--model-dir', type=str, default="./output/model", help='Path to the directory containing the model.')
    parser.add_argument('--dataset-dir', type=str, default="./output/dataset", help='Path to the dataset directory.')

    args = parser.parse_args()

    model_dir = args.model_dir
    dataset_dir = args.dataset_dir

    # Load the model and tokenizer
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_dir,
        max_seq_length=2048,
        load_in_4bit=True,
        dtype=None,
    )
    

    # Re-apply the chat template to the tokenizer
    tokenizer = get_chat_template(
        tokenizer,
        mapping={"role": "from", "content": "value", "user": "human", "assistant": "gpt"},
        chat_template="chatml",
    )

    # Load the dataset
    dataset = Dataset.load_from_disk(dataset_dir)

    # Ensure the dataset is not empty
    if len(dataset) == 0:
        print("The dataset is empty. Cannot proceed with evaluation.")
        return

    run_eval(model, tokenizer, dataset)
    

if __name__ == "__main__":
    main()
