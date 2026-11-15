# kopro-uranus-worker

RunPod serverless worker for **Kopro 5.0 Uranus**: llama.cpp server with the model baked into the image, so cold starts skip the download.

- Default: Qwen3.8-27B (UD-Q4_K_XL) with the Kopro LoRA adapter applied
- `variant: "base"`: the same model with the adapter switched off for that request (A/B evaluation, no extra VRAM)

Input (same contract as worker-ollama): `{messages, think, options?, tools?, variant?}` → Ollama `/api/chat`-shaped response.
`{warmup: true}` returns once the server is up.

Build: Actions → build-uranus-image → Run workflow (optional `adapter_url`).
