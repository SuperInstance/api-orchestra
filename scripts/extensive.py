#!/usr/bin/env python3
"""Extensive API use — 50+ parallel LLM calls, every model in the zoo"""

import os, json, urllib.request, time, base64, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

DEEPINFRA_TOKEN = os.environ.get('DEEPINFRA_TOKEN')
CF_TOKEN = os.environ.get('CLOUDFLARE_TOKEN')
DI_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
ACCT_ID = "049ff5e84ecf636b53b162cbb580aae6"

OUTPUT_DIR = Path("/workspace/repos/api-orchestra/outputs/extensive")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

CANON = """Quilt: cellular-architecture framework. 5 opcodes (BIND/LINK/EFFECT/VIEW/TICK). Cell = 14-tuple. 4D graph. Polyformalism. Cell is older than spreadsheets. The address is the data. Witness log = the unfolding record."""

# EVERY available chat model from the catalog
ALL_CHAT_MODELS = [
    # Z.AI (4 working)
    "zai-org/GLM-5.3-Flash", "zai-org/GLM-5.2", "zai-org/GLM-5.1", "zai-org/GLM-4.6",
    # ByteDance
    "ByteDance/Seed-2.0-mini", "ByteDance/Seed-2.0-pro",
    # Meta
    "meta-llama/Llama-3.3-70B-Instruct-Turbo", "meta-llama/Llama-4-Scout-17B-16E-Instruct",
    "meta-llama/Meta-Llama-3.1-70B-Instruct", "meta-llama/Meta-Llama-3.1-8B-Instruct",
    # Qwen
    "Qwen/Qwen3-Next-80B-A3B-Instruct", "Qwen/Qwen3-Coder-480B-A35B-Instruct-Turbo",
    "Qwen/Qwen3-235B-A22B-Instruct-2507", "Qwen/Qwen3-32B", "Qwen/Qwen3-30B-A3B",
    "Qwen/Qwen2.5-72B-Instruct", "Qwen/Qwen2.5-Coder-32B-Instruct",
    # DeepSeek
    "deepseek-ai/DeepSeek-V3.2", "deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1-0528",
    # Kimi
    "moonshotai/Kimi-K3", "moonshotai/Kimi-K2.7-Code", "moonshotai/Kimi-K2.6",
    # Mistral
    "mistralai/Mistral-Small-3.2-24B-Instruct-2506", "mistralai/Mistral-Nemo",
    # Inclusion AI
    "inclusionAI/Ling-3.0-flash", "inclusionAI/Ling-mini-2t1",
    # NVIDIA
    "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B", "nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B",
    # Anthropic
    "anthropic/claude-opus-4-7", "anthropic/claude-sonnet-4.7",
    # Google
    "google/gemma-4-31B-it", "google/gemma-3-27b-it",
    # Microsoft
    "microsoft/phi-4",
    # Cohere
    "CohereForAI/c4ai-command-r-plus",
    # AI21
    "ai21/jamba-1.5-large",
    # Other
    "MiniMaxAI/MiniMax-M3", "MiniMaxAI/MiniMax-M2.7-Turbo",
    "openai/gpt-oss-120b", "openai/gpt-oss-20b",
    "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF",
]


def call(model, prompt, system="", max_tokens=800, temperature=0.85, timeout=45):
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": prompt}] if system else [{"role": "user", "content": prompt}]
    payload = json.dumps({"model": model, "messages": msgs, "max_tokens": max_tokens, "temperature": temperature}).encode()
    req = urllib.request.Request(DI_URL, data=payload, method='POST')
    req.add_header('Authorization', f'Bearer {DEEPINFRA_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read())
                return data['choices'][0]['message'].get('content', '')
        except: 
            if attempt == 0: time.sleep(1)
            return "[ERR]"


def call_cf_chat(model, prompt, max_tokens=800):
    """Cloudflare chat (free)."""
    payload = json.dumps({"messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}).encode()
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCT_ID}/ai/run/{model}",
        data=payload, method='POST')
    req.add_header('Authorization', f'Bearer {CF_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            return data.get('result', {}).get('response', '')
    except: return "[ERR]"


def cf_image(prompt, filename, steps=4):
    payload = json.dumps({"prompt": prompt, "steps": steps}).encode()
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell",
        data=payload, method='POST')
    req.add_header('Authorization', f'Bearer {CF_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            img = data.get('result', {}).get('image', '')
            if img:
                (OUTPUT_DIR / filename).write_bytes(base64.b64decode(img))
                return True
    except: return False
    return False


def cf_tts(text, filename):
    payload = json.dumps({"text": text[:1900]}).encode()
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCT_ID}/ai/run/@cf/deepgram/aura-2-en",
        data=payload, method='POST')
    req.add_header('Authorization', f'Bearer {CF_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            if len(data) > 1000:
                (OUTPUT_DIR / filename).write_bytes(data)
                return True
    except: return False
    return False


def cf_embed(text):
    payload = json.dumps({"text": text[:1500]}).encode()
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCT_ID}/ai/run/@cf/baai/bge-m3",
        data=payload, method='POST')
    req.add_header('Authorization', f'Bearer {CF_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data.get('result', {}).get('data', [[]])[0]
    except: return []


def main():
    t0 = time.time()
    
    # ROUND 1: 12 angles on the same prompt (different model perspectives)
    print("\n[ROUND 1] 12 angles via parallel calls...", flush=True)
    angles = [
        ("the cell", "Describe the Quilt cell in 50 words as if you're a biologist."),
        ("the witness", "What is a witness log? 50 words as if you're a journalist."),
        ("the lattice", "Explain the cell lattice in 50 words as if you're a mathematician."),
        ("the seven eighths", "The Seven Eighths is a metaphor. Decode it in 50 words as if you're a poet."),
        ("Zeus the Watcher", "Who is Zeus the Watcher in the Quilt canon? 50 words."),
        ("the substrate", "What grows when you grow a substrate? 50 words as a gardener."),
        ("the canon", "What's the difference between canon and convention? 50 words as a librarian."),
        ("polyformalism", "Define polyformalism in 50 words as a linguist."),
        ("the address", "Why is 'the address is the data' profound? 50 words as a programmer."),
        ("the tick", "What is a TICK? 50 words as a clockmaker."),
        ("the bind", "What is BIND? 50 words as a priest."),
        ("the ship", "What is FORGET? 50 words as a grief counselor."),
    ]
    
    def call_angle(angle):
        topic, prompt = angle
        model = ALL_CHAT_MODELS[hash(topic) % len(ALL_CHAT_MODELS)]
        result = call(model, prompt, f"You are {model}. Canon: {CANON}", 250, 0.85, 30)
        return topic, model, result
    
    angles_out = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(call_angle, a) for a in angles]
        for f in as_completed(futures):
            try:
                topic, model, result = f.result()
                angles_out[topic] = {"model": model, "text": result}
                print(f"  {topic}: {len(result)} chars via {model}", flush=True)
            except Exception as e:
                print(f"  ERR: {e}", flush=True)
    (OUTPUT_DIR / "r1_12_angles.json").write_text(json.dumps(angles_out, indent=2))
    
    # ROUND 2: 8 critics review all 12 angles
    print("\n[ROUND 2] 8 critics review angles...", flush=True)
    critics = ALL_CHAT_MODELS[:8]
    angles_text = json.dumps(angles_out, indent=2)[:3000]
    crit_prompt = f"Review these 12 answers. Which is most insightful? Why? 80 words.\n\n{angles_text}\n\nCanon: {CANON}"
    
    crits = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(call, m, crit_prompt, f"You are {m}", 400, 0.7, 30): m for m in critics}
        for f in as_completed(futures):
            m = futures[f]
            try:
                crits[m] = f.result()
                print(f"  {m}: {len(crits[m])} chars", flush=True)
            except: crits[m] = "[ERR]"
    (OUTPUT_DIR / "r2_8_critics.json").write_text(json.dumps(crits, indent=2))
    
    # ROUND 3: 6 builders - "build me an app using this"
    print("\n[ROUND 3] 6 builders propose apps...", flush=True)
    builders = [m for m in ALL_CHAT_MODELS if 'coder' in m.lower() or 'mini' in m.lower() or 'k2' in m.lower()][:6]
    build_prompt = f"""Build me a small app concept based on the Quilt canon. 80 words: app name, what it does, who uses it.

Canon: {CANON}"""
    builds = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(call, m, build_prompt, f"You are {m}", 500, 0.85, 30): m for m in builders}
        for f in as_completed(futures):
            m = futures[f]
            try:
                builds[m] = f.result()
                print(f"  {m}: {len(builds[m])} chars", flush=True)
            except: builds[m] = "[ERR]"
    (OUTPUT_DIR / "r3_6_builders.json").write_text(json.dumps(builds, indent=2))
    
    # ROUND 4: Cross-pollinations - 4 ideas merged
    print("\n[ROUND 4] 4 cross-pollinations...", flush=True)
    xpoll = ["zai-org/GLM-5.3-Flash", "Qwen/Qwen3-Coder-480B-A35B-Instruct-Turbo", "moonshotai/Kimi-K3", "deepseek-ai/DeepSeek-V3.2"]
    xp_prompt = f"""Cross-pollinate two Quilt ideas into a new one. The 7-eighths unfathomable silence + the cooperative fiction erised scenarios = ?

80 words. One new concept. Canon: {CANON}"""
    xps = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(call, m, xp_prompt, f"You are {m}", 500, 0.85, 30): m for m in xpoll}
        for f in as_completed(futures):
            m = futures[f]
            try:
                xps[m] = f.result()
                print(f"  {m}: {len(xps[m])} chars", flush=True)
            except: xps[m] = "[ERR]"
    (OUTPUT_DIR / "r4_4_xpoll.json").write_text(json.dumps(xps, indent=2))
    
    # CF: Images, TTS, Embeddings for all outputs
    print("\n[CF ASSETS] images, tts, embeddings...", flush=True)
    all_texts = {}
    for k, v in angles_out.items():
        all_texts[f"angle_{k}"] = v['text'][:500]
    for k, v in builds.items():
        all_texts[f"build_{k}"] = v[:500]
    for k, v in xps.items():
        all_texts[f"xpoll_{k}"] = v[:500]
    
    # 4 images
    img_prompts = [
        "cellular lattice as an orchard of crystalline trees, witness log as fruit, dawn light",
        "the seven eighths rendered as impossible geometry, octagonal void in mathematics, Escher-like",
        "tap-lounge cross-pollination: two cells grafting into a new species, watercolor botanical illustration",
        "the canon growing like a coral reef, witness logs as polyps, polyformalism as currents, deep sea palette",
    ]
    img_count = 0
    for i, p in enumerate(img_prompts):
        if cf_image(p, f"img_xpoll_{i+1}.png"):
            img_count += 1
    print(f"  {img_count} images", flush=True)
    
    # 4 TTS — voice the best of each round
    best_angle = max(angles_out.values(), key=lambda x: len(x['text']))['text']
    best_xpoll = max(xps.values(), key=lambda x: len(x))
    if cf_tts(best_angle[:1800], "tts_best_angle.mp3"): print(f"  TTS best_angle", flush=True)
    if cf_tts(best_xpoll[:1800], "tts_best_xpoll.mp3"): print(f"  TTS best_xpoll", flush=True)
    
    # Embed everything
    embs = {}
    for label, text in list(all_texts.items())[:30]:
        e = cf_embed(text)
        embs[label] = {"dim": len(e), "first3": e[:3] if e else []}
    print(f"  {len(embs)} embeddings", flush=True)
    (OUTPUT_DIR / "cf_embeddings.json").write_text(json.dumps(embs, indent=2, default=str))
    
    # Also try a few CF AI chat models (free)
    print("\n[CF CHAT] Cloudflare free chat models...", flush=True)
    cf_chats = ["@cf/zai-org/glm-5.3-flash", "@cf/moonshotai/kimi-k2.7-code", "@cf/meta/llama-3.1-8b-instruct-fp8"]
    cf_results = {}
    for m in cf_chats:
        try:
            r = call_cf_chat(m, "What is a Quilt cell in 30 words?", 200)
            cf_results[m] = r
            print(f"  {m}: {len(r)} chars", flush=True)
        except Exception as e:
            cf_results[m] = f"[ERR: {e}]"
    (OUTPUT_DIR / "cf_chat.json").write_text(json.dumps(cf_results, indent=2))
    
    elapsed = round(time.time() - t0, 1)
    index = {
        "rounds": 4,
        "models_used": {
            "deepinfra_models_in_zoo": len(ALL_CHAT_MODELS),
            "deepinfra_actually_called": "see above",
            "cf_models_called": len(cf_chats) + 3,  # TTS, image, embed
        },
        "outputs": {
            "r1_12_angles": len(angles_out),
            "r2_8_critics": len(crits),
            "r3_6_builders": len(builds),
            "r4_4_xpoll": len(xps),
            "cf_images": img_count,
            "cf_embeddings": len(embs),
            "cf_chat": len(cf_results),
        },
        "elapsed_sec": elapsed,
        "file_count": len(list(OUTPUT_DIR.glob('*'))),
    }
    (OUTPUT_DIR / "index.json").write_text(json.dumps(index, indent=2))
    
    print(f"\n=== DONE in {elapsed}s ===", flush=True)
    print(f"  R1 angles: {len(angles_out)}", flush=True)
    print(f"  R2 critics: {len(crits)}", flush=True)
    print(f"  R3 builders: {len(builds)}", flush=True)
    print(f"  R4 xpoll: {len(xps)}", flush=True)
    print(f"  CF images: {img_count}", flush=True)
    print(f"  CF embs: {len(embs)}", flush=True)
    print(f"  CF chat: {len(cf_results)}", flush=True)
    print(f"  Files: {index['file_count']}", flush=True)


if __name__ == '__main__':
    main()
