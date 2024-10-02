#from nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04
#from golang:latest

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    pip \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch and transformers
RUN pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121
RUN pip3 install transformers

RUN pip3 install --upgrade pip
RUN pip3 install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
RUN pip3 install --no-deps "trl<0.9.0" peft accelerate bitsandbytes
RUN pip3 install -U xformers --index-url https://download.pytorch.org/whl/cu121
RUN pip3 install PyYAML

# Ollama via llama.cpp - ggml conversion tools
RUN git clone --recursive https://github.com/ggerganov/llama.cpp
RUN cd llama.cpp && make clean && make all -j

#Custom Python
ADD ./sliding_window.py .
ADD ./format_data_for_training.py .
ADD ./train.py .
ADD ./eval.py .
ADD ./util.py .
ADD ./create_dataset.py .
ADD ./save_gguf.sh .
ADD ./llama_data_pre_processing.py .
ADD ./llama_prompts.py .