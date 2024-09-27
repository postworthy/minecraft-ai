#!/bin/bash
cd "$(dirname "$0")"

./build.sh
docker run -it --shm-size=2gb --gpus all \
    --mount type=bind,source=$(pwd)/docker_models_cache/.cache/,target=/root/.cache/ \
    --mount type=bind,source=$(pwd)/input/,target=/app/input/ \
    --mount type=bind,source=$(pwd)/output/,target=/app/output/ \
    minecraft-ai-data-pipeline:latest bash