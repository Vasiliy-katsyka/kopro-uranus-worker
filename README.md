# kopro-uranus-worker

RunPod serverless worker for **Kopro 5.0 Uranus**: Ollama with the model baked into the image, so cold starts skip the download.

- `kopro-uranus`: Qwen3.8-27B (UD-Q4_K_XL) + Kopro LoRA adapter
- `kopro-uranus-base`: the same base model without the adapter (A/B evaluation)

Input (same contract as worker-ollama): `{messages, think, options?, tools?, variant?: "base"}` → Ollama `/api/chat` response.
`{warmup: true}` loads the model into VRAM and returns.

Build: Actions → build-uranus-image → Run workflow (optional `adapter_url`).
