import argparse
import os
import random
import torch
from datasets import Dataset
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
from util import get_unique_function


def main():
    parser = argparse.ArgumentParser(description='LLM save to gguf')
    parser.add_argument('--model-dir', type=str, default="./output/model", help='Path to the directory containing the model.')

    args = parser.parse_args()

    model_dir = args.model_dir

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

    model_dir = model_dir.removesuffix('/').removesuffix('\\') + "-gguf"

    model.save_pretrained_gguf(model_dir, tokenizer)


if __name__ == "__main__":
    main()
