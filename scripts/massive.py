#!/usr/bin/env python3
"""Massive parallel — 100+ API calls, 30+ models, 5 modalities"""

import os, json, urllib.request, time, base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

DEEPINFRA_TOKEN = os.environ.get('DEEPINFRA_TOKEN')
CF_TOKEN = os.environ.get('CLOUDFLARE_TOKEN')
DI_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
ACCT_ID = "049ff5e84ecf636b53b162cbb580aae6"
OUTPUT_DIR = Path("/workspace/repos/api-orchestra/outputs/massive")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

CANON = """Quilt: cellular-architecture framework. 5 opcodes (BIND/LINK/EFFECT/VIEW/TICK). Cell = 14-tuple. 4D graph. Polyformalism."""

# ALL available chat models — 35 total
ALL_MODELS = [
    "ByteDance/Seed-2.0-mini", "ByteDance/Seed-2.0-pro",
    "meta-llama/Llama-3.3-70B-Instruct-Turbo", "meta-llama/Llama-4-Scout-17B-16E-Instruct",
    "meta-llama/Meta-Llama-3.1-70B-Instruct", "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "Qwen/Qwen3-Next-80B-A3B-Instruct", "Qwen/Qwen3-Coder-480B-A35B-Instruct-Turbo",
    "Qwen/Qwen3-235B-A22B-Instruct-2507", "Qwen/Qwen3-32B", "Qwen/Qwen3-30B-A3B",
    "deepseek-ai/DeepSeek-V3.2", "deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1-0528",
    "moonshotai/Kimi-K3", "moonshotai/Kimi-K2.7-Code", "moonshotai/Kimi-K2.6",
    "mistralai/Mistral-Small-3.2-24B-Instruct-2506", "mistralai/Mistral-Nemo",
    "inclusionAI/Ling-3.0-flash", "inclusionAI/Ling-mini-2t1",
    "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B", "nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B",
    "anthropic/claude-opus-4-7", "anthropic/claude-sonnet-4.7",
    "google/gemma-4-31B-it", "google/gemma-3-27b-it",
    "zai-org/GLM-5.3-Flash", "zai-org/GLM-5.2", "zai-org/GLM-5.1", "zai-org/GLM-4.6",
    "MiniMaxAI/MiniMax-M3", "MiniMaxAI/MiniMax-M2.7-Turbo",
    "openai/gpt-oss-120b", "openai/gpt-oss-20b",
    "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF",
]


def call(model, prompt, system="", max_tokens=400, temperature=0.85, timeout=30):
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": prompt}] if system else [{"role": "user", "content": prompt}]
    payload = json.dumps({"model": model, "messages": msgs, "max_tokens": max_tokens, "temperature": temperature}).encode()
    req = urllib.request.Request(DI_URL, data=payload, method='POST')
    req.add_header('Authorization', f'Bearer {DEEPINFRA_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            return data['choices'][0]['message'].get('content', '')
    except:
        return "[ERR]"


def main():
    t0 = time.time()
    
    # Round 1: ALL 35 models answer one question
    print(f"\n[ROUND 1] ALL {len(ALL_MODELS)} models answer: 'What is a Quilt cell in 30 words?'", flush=True)
    prompt = f"What is a Quilt cell in 30 words? Use this canon: {CANON}"
    
    r1 = {}
    with ThreadPoolExecutor(max_workers=15) as ex:
        futures = {ex.submit(call, m, prompt, f"You are {m}", 200, 0.7, 30): m for m in ALL_MODELS}
        for f in as_completed(futures):
            m = futures[f]
            try:
                r1[m] = f.result()
                print(f"  {m}: {len(r1[m]) if r1[m] and not r1[m].startswith('[') else 'ERR'}", flush=True)
            except: r1[m] = "[ERR]"
    (OUTPUT_DIR / "r1_all_35_answers.json").write_text(json.dumps(r1, indent=2))
    
    # Round 2: Voting — which 3 answers were best?
    print(f"\n[ROUND 2] Models vote on best 3...", flush=True)
    answers_text = json.dumps(r1, indent=2)[:3500]
    vote_prompt = f"From these answers to 'What is a Quilt cell?', pick the top 3. Justify in 80 words.\n\n{answers_text}"
    
    voters = ALL_MODELS[:10]
    r2 = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(call, m, vote_prompt, f"You are {m}", 600, 0.7, 30): m for m in voters}
        for f in as_completed(futures):
            m = futures[f]
            try:
                r2[m] = f.result()
                print(f"  {m}: {len(r2[m]) if r2[m] and not r2[m].startswith('[') else 'ERR'}", flush=True)
            except: r2[m] = "[ERR]"
    (OUTPUT_DIR / "r2_votes.json").write_text(json.dumps(r2, indent=2))
    
    # Round 3: 20 different haiku — one per model
    print(f"\n[ROUND 3] 20 haiku in parallel...", flush=True)
    haiku_prompt = f"Write a haiku about the Quilt cell. Use this canon: {CANON}"
    
    r3 = {}
    with ThreadPoolExecutor(max_workers=15) as ex:
        futures = {ex.submit(call, m, haiku_prompt, f"You are {m}", 100, 0.85, 30): m for m in ALL_MODELS[:20]}
        for f in as_completed(futures):
            m = futures[f]
            try:
                r3[m] = f.result()
                print(f"  {m}: {len(r3[m]) if r3[m] and not r3[m].startswith('[') else 'ERR'}", flush=True)
            except: r3[m] = "[ERR]"
    (OUTPUT_DIR / "r3_haikus.json").write_text(json.dumps(r3, indent=2))
    
    # CF Massive: 10 images, 10 TTS, 30 embeddings
    print(f"\n[CF MASSIVE] 10 images, 10 TTS, 30 embeddings...", flush=True)
    
    img_prompts = [
        f"Quilt cellular lattice variation {i+1}: abstract geometric pattern with witness log threads, color palette: {'blue-gold' if i%2==0 else 'warm-orange-indigo'}"
        for i in range(10)
    ]
    
    def cf_image(p, i):
        payload = json.dumps({"prompt": p, "steps": 4}).encode()
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
                    (OUTPUT_DIR / f"img_massive_{i+1}.png").write_bytes(base64.b64decode(img))
                    return True
        except: return False
        return False
    
    img_count = 0
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(cf_image, p, i): i for i, p in enumerate(img_prompts)}
        for f in as_completed(futures):
            if f.result(): img_count += 1
    print(f"  {img_count} images", flush=True)
    
    # 10 TTS
    tts_texts = [f"This is haiku number {i+1}, voiced by Cloudflare Aura Two." for i in range(10)]
    
    def cf_tts(text, i):
        payload = json.dumps({"text": text}).encode()
        req = urllib.request.Request(
            f"https://api.cloudflare.com/client/v4/accounts/{ACCT_ID}/ai/run/@cf/deepgram/aura-2-en",
            data=payload, method='POST')
        req.add_header('Authorization', f'Bearer {CF_TOKEN}')
        req.add_header('Content-Type', 'application/json')
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
                if len(data) > 1000:
                    (OUTPUT_DIR / f"tts_massive_{i+1}.mp3").write_bytes(data)
                    return True
        except: return False
        return False
    
    tts_count = 0
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(cf_tts, t, i): i for i, t in enumerate(tts_texts)}
        for f in as_completed(futures):
            if f.result(): tts_count += 1
    print(f"  {tts_count} TTS", flush=True)
    
    # 30 embeddings
    def cf_embed(text, label):
        payload = json.dumps({"text": text[:1500]}).encode()
        req = urllib.request.Request(
            f"https://api.cloudflare.com/client/v4/accounts/{ACCT_ID}/ai/run/@cf/baai/bge-m3",
            data=payload, method='POST')
        req.add_header('Authorization', f'Bearer {CF_TOKEN}')
        req.add_header('Content-Type', 'application/json')
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                emb = data.get('result', {}).get('data', [[]])[0]
                return label, len(emb), emb[:3] if emb else []
        except: return label, 0, []
    
    embed_texts = {f"r1_{k}": v[:500] for k, v in r1.items() if v and not v.startswith('[') and len(v) > 50}
    embed_texts.update({f"r3_{k}": v[:500] for k, v in r3.items() if v and not v.startswith('[') and len(v) > 50})
    
    embs = {}
    items = list(embed_texts.items())[:30]
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(cf_embed, v, k): k for k, v in items}
        for f in as_completed(futures):
            label, dim, first = f.result()
            embs[label] = {"dim": dim, "first3": first}
    print(f"  {len(embs)} embeddings", flush=True)
    (OUTPUT_DIR / "cf_emb_massive.json").write_text(json.dumps(embs, indent=2, default=str))
    
    elapsed = round(time.time() - t0, 1)
    index = {
        "rounds": 3,
        "models_in_zoo": len(ALL_MODELS),
        "r1_answers": sum(1 for v in r1.values() if v and not v.startswith('[') and len(v) > 50),
        "r2_votes": sum(1 for v in r2.values() if v and not v.startswith('[') and len(v) > 50),
        "r3_haikus": sum(1 for v in r3.values() if v and not v.startswith('[') and len(v) > 50),
        "cf_images": img_count,
        "cf_tts": tts_count,
        "cf_embeddings": len(embs),
        "elapsed_sec": elapsed,
        "file_count": len(list(OUTPUT_DIR.glob('*'))),
        "total_calls": sum(1 for v in r1.values() if v) + sum(1 for v in r2.values() if v) + sum(1 for v in r3.values() if v) + img_count + tts_count + len(embs),
    }
    (OUTPUT_DIR / "index.json").write_text(json.dumps(index, indent=2))
    print(f"\n=== DONE in {elapsed}s ===", flush=True)
    print(f"  Total API calls: {index['total_calls']}", flush=True)
    print(f"  Files: {index['file_count']}", flush=True)


if __name__ == '__main__':
    main()
