"""RunPod handler with the same contract as worker-ollama (what Kopro's main.py already sends):
{messages, think, stream:false, options?, tools?}  ->  Ollama /api/chat-shaped items
(message.content / message.tool_calls / eval_duration / prompt_eval_duration).

It is a generator with return_aggregate_stream, so:
- /run + /status returns the list of items (main.py concatenates message.content), same as before;
- with {stream_chunks: true}, text is yielded in ~0.35 s batches so /stream shows the answer as it is written.
{variant: "base"} turns the Kopro LoRA off for that request (A/B eval). {warmup: true} returns once the server is up."""
import json, os, time, requests, runpod

URL = "http://127.0.0.1:8080"
HAS_LORA = os.path.exists("/models/adapter.gguf")
SYSTEM = os.environ.get("SYSTEM_PROMPT", "You are Kopro 5.0 Uranus, an AI assistant made by Vasiliy Katsyka at Kopro AI. Answer in the user's language.")
FLUSH_S = 0.35


def build(inp):
    msgs = inp.get("messages", [])
    if not msgs or msgs[0].get("role") != "system":
        msgs = [{"role": "system", "content": SYSTEM}] + msgs
    o = inp.get("options") or {}
    body = {"messages": msgs,
            "temperature": o.get("temperature", 0.7), "top_p": o.get("top_p", 0.8), "top_k": o.get("top_k", 20),
            "chat_template_kwargs": {"enable_thinking": bool(inp.get("think", False))}}
    if (o.get("num_predict") or -1) > 0:
        body["max_tokens"] = o["num_predict"]
    if inp.get("tools"):
        body["tools"] = inp["tools"]
    base = inp.get("variant") == "base"
    if HAS_LORA:
        body["lora"] = [{"id": 0, "scale": 0.0 if base else 1.0}]
    return body, ("kopro-uranus-base" if base or not HAS_LORA else "kopro-uranus")


def final_item(model, content, tool_calls, timings, completion_tokens):
    msg = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return {"model": model, "message": msg, "done": True, "eval_count": completion_tokens,
            "eval_duration": int((timings.get("predicted_ms") or 0) * 1e6),
            "prompt_eval_duration": int((timings.get("prompt_ms") or 0) * 1e6)}


def handler(job):
    inp = job["input"] or {}
    if inp.get("warmup"):
        requests.get(URL + "/health", timeout=300)
        yield {"warm": True}
        return
    body, model = build(inp)

    if not inp.get("stream_chunks") or inp.get("tools"):
        body["stream"] = False
        r = requests.post(URL + "/v1/chat/completions", json=body, timeout=900)
        if r.status_code >= 400:  # keep llama-server's reason (e.g. tool-call parse error) in the job error
            raise RuntimeError(f"{r.status_code} Server Error: {r.text[:500]}")
        d = r.json()
        m = d["choices"][0]["message"]
        calls = [{"function": {"name": c["function"]["name"], "arguments": json.loads(c["function"].get("arguments") or "{}")}}
                 for c in (m.get("tool_calls") or [])]
        yield final_item(model, m.get("content") or "", calls, d.get("timings") or {}, (d.get("usage") or {}).get("completion_tokens", 0))
        return

    body["stream"] = True
    buf, last, timings, ntok = "", time.time(), {}, 0
    with requests.post(URL + "/v1/chat/completions", json=body, stream=True, timeout=900) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line.startswith(b"data: "):
                continue
            data = line[6:]
            if data.strip() == b"[DONE]":
                break
            j = json.loads(data)
            timings = j.get("timings") or timings
            if j.get("choices"):
                delta = (j["choices"][0].get("delta") or {}).get("content") or ""
                if delta:
                    buf += delta
                    ntok += 1
            if buf and time.time() - last >= FLUSH_S:
                yield {"message": {"role": "assistant", "content": buf}}
                buf, last = "", time.time()
    yield final_item(model, buf, [], timings, ntok)


runpod.serverless.start({"handler": handler, "return_aggregate_stream": True})
