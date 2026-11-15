#!/bin/bash
# Start llama-server (model fully on GPU), wait until it is healthy, then run the RunPod handler.
LORA=(); [ -f /models/adapter.gguf ] && LORA=(--lora /models/adapter.gguf --lora-init-without-apply)
/app/llama-server -m /models/base.gguf "${LORA[@]}" -ngl 999 -c 32768 --parallel 2 -fa on -ctk q8_0 -ctv q8_0 \
  --jinja --host 127.0.0.1 --port 8080 --no-webui > /tmp/llama.log 2>&1 &
for i in $(seq 600); do curl -sf localhost:8080/health >/dev/null && break; sleep 0.5; done
exec python3 -u /app/handler.py
