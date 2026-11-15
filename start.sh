#!/bin/bash
# Start Ollama, load the model into VRAM before taking jobs, then run the RunPod handler.
ollama serve >/tmp/ollama.log 2>&1 &
for i in $(seq 120); do curl -s localhost:11434 >/dev/null && break; sleep 0.5; done
curl -s localhost:11434/api/chat -d '{"model":"kopro-uranus","messages":[],"keep_alive":-1}' >/dev/null
exec python3 -u /app/handler.py
