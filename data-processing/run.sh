#!/bin/bash
cd "$(dirname "$0")"

HOST_IP=$(hostname -I | awk '{print $1}')

./build.sh
docker run -it --shm-size=2gb --gpus all \
    -e "OLLAMA_URL=http://${HOST_IP}:5555/" \
    --mount type=bind,source=$(pwd)/docker_models_cache/.cache/,target=/root/.cache/ \
    --mount type=bind,source=/mnt/h/minecraft-ai-training/input/,target=/app/input/ \
    --mount type=bind,source=/mnt/h/minecraft-ai-training/output/,target=/app/output/ \
    minecraft-ai-data-pipeline:latest bash