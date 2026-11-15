"""RunPod handler with the same contract as worker-ollama (what Kopro's main.py already sends):
{messages, think, stream:false, options?, tools?}  ->  Ollama /api/chat-shaped dict
(message.content / message.tool_calls / eval_duration / prompt_eval_duration).
{variant: "base"} turns the Kopro LoRA off for that request (A/B eval). {warmup: true} returns once the server is up."""
import json, os, requests, runpod

URL = "http://127.0.0.1:8080"
HAS_LORA = os.path.exists("/models/adapter.gguf")
SYSTEM = "You are Kopro 5.0 Uranus, an AI assistant made by Vasiliy Katsyka at Kopro AI. Answer in the user's language."


def handler(job):
    inp = job["input"] or {}
    if inp.get("warmup"):
        requests.get(URL + "/health", timeout=300)
        return {"warm": True}
    msgs = inp.get("messages", [])
    if not msgs or msgs[0].get("role") != "system":
        msgs = [{"role": "system", "content": SYSTEM}] + msgs
    o = inp.get("options") or {}
    body = {"messages": msgs, "stream": False,
            "temperature": o.get("temperature", 0.7), "top_p": o.get("top_p", 0.8), "top_k": o.get("top_k", 20),
            "chat_template_kwargs": {"enable_thinking": bool(inp.get("think", False))}}
    if (o.get("num_predict") or -1) > 0:
        body["max_tokens"] = o["num_predict"]
    if inp.get("tools"):
        body["tools"] = inp["tools"]
    base = inp.get("variant") == "base"
    if HAS_LORA:
        body["lora"] = [{"id": 0, "scale": 0.0 if base else 1.0}]
    r = requests.post(URL + "/v1/chat/completions", json=body, timeout=900)
    r.raise_for_status()
    d = r.json()
    m = d["choices"][0]["message"]
    msg = {"role": "assistant", "content": m.get("content") or ""}
    if m.get("tool_calls"):
        msg["tool_calls"] = [{"function": {"name": c["function"]["name"],
                                           "arguments": json.loads(c["function"].get("arguments") or "{}")}}
                             for c in m["tool_calls"]]
    t = d.get("timings") or {}
    return {"model": "kopro-uranus-base" if base or not HAS_LORA else "kopro-uranus",
            "message": msg, "done": True,
            "eval_count": (d.get("usage") or {}).get("completion_tokens", 0),
            "eval_duration": int(t.get("predicted_ms", 0) * 1e6),
            "prompt_eval_duration": int(t.get("prompt_ms", 0) * 1e6)}


runpod.serverless.start({"handler": handler})
