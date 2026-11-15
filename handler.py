"""RunPod handler, same input contract as worker-ollama that main.py already uses:
{messages, think, stream:false, options?, tools?}  ->  Ollama /api/chat response dict.
{variant: "base"} uses the raw base model (A/B eval); default is the fine-tuned "kopro-uranus".
{warmup: true} returns as soon as the model is in VRAM (used by the chat's pre-warm ping)."""
import requests, runpod

OLLAMA = "http://localhost:11434/api/chat"

def handler(job):
    inp = job["input"] or {}
    if inp.get("warmup"):
        requests.post(OLLAMA, json={"model": "kopro-uranus", "messages": [], "keep_alive": -1}, timeout=300)
        return {"warm": True}
    model = "kopro-uranus-base" if inp.get("variant") == "base" else "kopro-uranus"
    body = {"model": model, "messages": inp.get("messages", []), "stream": False,
            "think": bool(inp.get("think", False)), "keep_alive": -1}
    if inp.get("options"):
        body["options"] = inp["options"]
    if inp.get("tools"):
        body["tools"] = inp["tools"]
    r = requests.post(OLLAMA, json=body, timeout=900)
    r.raise_for_status()
    return r.json()

runpod.serverless.start({"handler": handler})
