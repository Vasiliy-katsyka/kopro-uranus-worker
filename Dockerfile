# Kopro 5.0 Uranus serverless worker: Ollama with the model baked into the image (no download on cold start).
FROM ollama/ollama:0.40.13
LABEL org.opencontainers.image.source=https://github.com/Vasiliy-katsyka/kopro-uranus-worker
ARG BASE_URL=https://huggingface.co/unsloth/Qwen3.8-27B-GGUF/resolve/main/Qwen3.8-27B-UD-Q4_K_XL.gguf
ARG ADAPTER_URL=
RUN apt-get update && apt-get install -y --no-install-recommends python3-pip curl ca-certificates && rm -rf /var/lib/apt/lists/* \
 && pip3 install --no-cache-dir --break-system-packages runpod==1.7.13 requests
ENV OLLAMA_MODELS=/models OLLAMA_KEEP_ALIVE=-1 OLLAMA_NUM_PARALLEL=2 OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0
COPY Modelfile Modelfile.base handler.py start.sh /app/
# download + create + delete in ONE layer so the raw GGUF isn't stored twice
RUN mkdir -p /tmp/m && curl -fL --retry 5 -o /tmp/m/base.gguf "$BASE_URL" \
 && if [ -n "$ADAPTER_URL" ]; then curl -fL --retry 5 -o /tmp/m/adapter.gguf "$ADAPTER_URL"; fi \
 && (ollama serve >/tmp/ollama.log 2>&1 &) && for i in $(seq 60); do curl -s localhost:11434 >/dev/null && break; sleep 1; done \
 && cd /tmp/m && ollama create kopro-uranus-base -f /app/Modelfile.base \
 && if [ -f /tmp/m/adapter.gguf ]; then ollama create kopro-uranus -f /app/Modelfile; else ollama cp kopro-uranus-base kopro-uranus; fi \
 && ollama list && rm -rf /tmp/m
ENTRYPOINT ["/bin/bash", "/app/start.sh"]
