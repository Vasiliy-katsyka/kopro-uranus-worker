# Kopro 5.0 Uranus serverless worker: llama.cpp server with the model baked into the image (no download on cold start).
# One copy of Qwen3.8-27B in VRAM; the Kopro LoRA is switched on/off per request (fine-tuned vs base A/B).
FROM ghcr.io/ggml-org/llama.cpp:server-cuda12-b12030
LABEL org.opencontainers.image.source=https://github.com/Vasiliy-katsyka/kopro-uranus-worker
ARG BASE_URL=https://huggingface.co/unsloth/Qwen3.8-27B-GGUF/resolve/main/Qwen3.8-27B-UD-Q4_K_XL.gguf
ARG ADAPTER_URL=
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip curl ca-certificates && rm -rf /var/lib/apt/lists/* \
 && (pip3 install --no-cache-dir --break-system-packages runpod==1.7.13 requests || pip3 install --no-cache-dir runpod==1.7.13 requests)
RUN mkdir -p /models && curl -fL --retry 5 -o /models/base.gguf "$BASE_URL"
RUN if [ -n "$ADAPTER_URL" ]; then curl -fL --retry 5 -o /models/adapter.gguf "$ADAPTER_URL"; fi
COPY handler.py start.sh /app/
ENTRYPOINT ["/bin/bash", "/app/start.sh"]
