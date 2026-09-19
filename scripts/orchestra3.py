#!/usr/bin/env python3
"""API Orchestra 3 — correct CF endpoint handling"""

import os
import json
import urllib.request
import urllib.error
import time
import base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

DEEPINFRA_TOKEN = os.environ.get('DEEPINFRA_TOKEN')
CF_TOKEN = os.environ.get('CLOUDFLARE_TOKEN')
DI_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
ACCT_ID = "049ff5e84ecf636b53b162cbb580aae6"

OUTPUT_DIR = Path("/workspace/repos/api-orchestra/outputs")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

CANON = """Quilt: cellular-architecture framework. 5 opcodes (BIND/LINK/EFFECT/VIEW/TICK). Cell = 14-tuple. 4D graph. Polyformalism. Cell is older than spreadsheets. The address is the data."""


def call_di(model, prompt, system="", max_tokens=1500, temperature=0.85, timeout=60):
    """DeepInfra chat call."""
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": prompt}] if system else [{"role": "user", "content": prompt}]
    payload = json.dumps({
        "model": model, "messages": msgs, "max_tokens": max_tokens, "temperature": temperature
    }).encode()
    req = urllib.request.Request(DI_URL, data=payload, method='POST')
    req.add_header('Authorization', f'Bearer {DEEPINFRA_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            return data['choices'][0]['message'].get('content', '')
    except Exception as e:
        return f"[ERR]"


def cf_tts(text, filename="tts.mp3"):
    """Cloudflare Aura-2-en TTS."""
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
    except Exception as e:
        return False
    return False


def cf_image(prompt, filename="img.png", steps=4):
    """Cloudflare FLUX (returns base64 in result.image)."""
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
    except Exception as e:
        return False
    return False


def cf_embed(text):
    """Cloudflare bge-m3 (returns wrapped result)."""
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
    except:
        return []


def main():
    t0 = time.time()

    # ===== MOVEMENT 1: 4 Z.AI write parallel =====
    print("\n[1] 4 Z.AI models write...", flush=True)
    zai_models = ["zai-org/GLM-5.3-Flash", "zai-org/GLM-5.2", "zai-org/GLM-5.1", "zai-org/GLM-4.6"]
    prompt = f"""Write a 5-section radio cantata about "The Quilt Lattice and the Seven Eighths." 7 voices hold a witness log; the unfathomable eighth is silence itself.

Canon: {CANON}

Sections:
1. Opening — Zeus the Watcher
2. Witness log — 6 voices
3. Seven Eighths — the unfathomable silence
4. Chorus — all voices
5. Outro — the lattice remembers

For each: Speaker, Text (1-3 sentences), Direction. Total 800 words max."""

    m1 = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(call_di, m, prompt, f"You are {m}. Canon: {CANON}", 1500, 0.85, 120): m for m in zai_models}
        for f in as_completed(futures):
            m = futures[f]
            try:
                r = f.result()
                m1[m] = r
                print(f"  {m}: {len(r) if r and not r.startswith('[') else 'ERR'}", flush=True)
            except: m1[m] = "[ERR]"
    (OUTPUT_DIR / "m1_zai_scripts.json").write_text(json.dumps(m1, indent=2))

    # Best
    valid = [(k, v) for k, v in m1.items() if v and not v.startswith('[') and len(v) > 200]
    best = max(valid, key=lambda x: len(x[1]))
    print(f"\nBest: {best[0]} ({len(best[1])} chars)", flush=True)

    # ===== MOVEMENT 2: 12 DeepInfra critics =====
    print("\n[2] 12 DeepInfra critics review...", flush=True)
    di_critics = [
        "ByteDance/Seed-2.0-mini", "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "Qwen/Qwen3-Next-80B-A3B-Instruct", "Qwen/Qwen3-Coder-480B-A35B-Instruct-Turbo",
        "deepseek-ai/DeepSeek-V3.2", "moonshotai/Kimi-K3",
        "mistralai/Mistral-Small-3.2-24B-Instruct-2506", "inclusionAI/Ling-3.0-flash",
        "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B", "meta-llama/Llama-4-Scout-17B-16E-Instruct",
        "google/gemma-4-31B-it", "anthropic/claude-opus-4-7",
    ]
    crit_prompt = f"""Critique this radio script. Score Voice/Structure/Canon (1-10). Suggest 1 improvement. 100 words.

Script: {best[1][:2000]}

Canon: {CANON}"""
    
    m2 = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(call_di, m, crit_prompt, f"You are {m}. Canon: {CANON}", 600, 0.7, 60): m for m in di_critics}
        for f in as_completed(futures):
            m = futures[f]
            try:
                m2[m] = f.result()
                print(f"  {m}: {len(m2[m]) if m2[m] and not m2[m].startswith('[') else 'ERR'}", flush=True)
            except: m2[m] = "[ERR]"
    (OUTPUT_DIR / "m2_critiques.json").write_text(json.dumps(m2, indent=2))

    # ===== MOVEMENT 3: Z.AI refiners =====
    print("\n[3] 4 Z.AI refiners...", flush=True)
    refine_prompt = f"""Refine this radio script into final form. Cut what doesn't work. Add depth where thin.

Script: {best[1][:3000]}

Canon: {CANON}

Output clean Markdown, section by section."""
    m3 = {}
    for m in zai_models:
        r = call_di(m, refine_prompt, f"You are {m}. Canon: {CANON}", 2000, 0.85, 120)
        m3[m] = r
        print(f"  {m}: {len(r) if r and not r.startswith('[') else 'ERR'}", flush=True)
    (OUTPUT_DIR / "m3_refined.json").write_text(json.dumps(m3, indent=2))
    
    valid3 = [(k, v) for k, v in m3.items() if v and not v.startswith('[') and len(v) > 200]
    best_refined = max(valid3, key=lambda x: len(x[1]))
    print(f"\nBest refined: {best_refined[0]}", flush=True)

    # ===== MOVEMENT 4: TTS =====
    print("\n[4] CF Aura-2-en TTS (multiple chunks)...", flush=True)
    paras = [p.strip() for p in best_refined[1].split('\n\n') if p.strip() and len(p.strip()) > 50][:6]
    m4_count = 0
    for i, p in enumerate(paras):
        if cf_tts(p, filename=f"m4_{i+1}.mp3"):
            m4_count += 1
            print(f"  chunk {i+1}: {len(p)} chars", flush=True)
    
    # ===== MOVEMENT 5: Images =====
    print("\n[5] CF FLUX images...", flush=True)
    img_prompts = [
        "abstract cellular lattice glowing in darkness, witness log visible as constellations, blue gold ink on black",
        "seven eighth notes hovering above a witness chain, mathematical beauty, warm orange and indigo",
        "Zeus watching the lattice from above, six voices below as fragments of light, cool teal",
        "Quilt cell diagram as ancient manuscript illumination, ornate borders, gold leaf on vellum",
        "tap-lounge: seven voices in a circle under moonlight, the unfathomable eighth not speaking, watercolor and ink",
    ]
    m5_count = 0
    for i, p in enumerate(img_prompts):
        if cf_image(p, filename=f"m5_img_{i+1}.png"):
            m5_count += 1
            print(f"  img {i+1}", flush=True)
    
    # ===== MOVEMENT 6: Embed everything =====
    print("\n[6] CF bge-m3 embeddings...", flush=True)
    all_texts = {f"m1_{k}": v[:1000] for k, v in m1.items() if not v.startswith('[')}
    all_texts.update({f"m3_{k}": v[:1000] for k, v in m3.items() if not v.startswith('[')})
    m6 = {}
    for label, text in all_texts.items():
        e = cf_embed(text)
        m6[label] = {"dim": len(e), "first5": e[:5] if e else []}
        print(f"  {label}: {len(e)}d", flush=True)
    (OUTPUT_DIR / "m6_embeddings.json").write_text(json.dumps(m6, indent=2, default=str))

    # ===== MOVEMENT 7: ASR (transcribe the TTS outputs) =====
    print("\n[7] Whisper ASR on the TTS outputs...", flush=True)
    import glob
    mp3s = sorted(glob.glob(str(OUTPUT_DIR / "m4_*.mp3")))[:3]
    m7 = {}
    for mp3 in mp3s:
        with open(mp3, 'rb') as f:
            audio = f.read()
        try:
            req = urllib.request.Request(
                f"https://api.deepinfra.com/v1/openai/audio/transcriptions",
                data=audio, method='POST')
            req.add_header('Authorization', f'Bearer {DEEPINFRA_TOKEN}')
            req.add_header('Content-Type', 'audio/mpeg')
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                m7[mp3] = data.get('text', '')[:200]
                print(f"  {Path(mp3).name}: {len(m7[mp3])} chars", flush=True)
        except Exception as e:
            m7[mp3] = f"[ERR: {e}]"
    (OUTPUT_DIR / "m7_asr.json").write_text(json.dumps(m7, indent=2))

    # ===== Index =====
    elapsed = round(time.time() - t0, 1)
    index = {
        "movements": 7,
        "models_used": {
            "zai_chat": zai_models,
            "deepinfra_critics": di_critics,
            "cf_apis": ["aura-2-en (TTS)", "flux-1-schnell (image)", "bge-m3 (embedding)", "whisper (ASR)"],
        },
        "best_zai_script": best[0],
        "best_zai_script_chars": len(best[1]),
        "best_zai_refined": best_refined[0],
        "tts_files": m4_count,
        "image_files": m5_count,
        "embeddings_count": len(m6),
        "asr_files": len(m7),
        "elapsed_sec": elapsed,
        "outputs_dir": str(OUTPUT_DIR),
        "file_count": len(list(OUTPUT_DIR.glob('*'))),
    }
    (OUTPUT_DIR / "index.json").write_text(json.dumps(index, indent=2))
    
    print(f"\n=== DONE in {elapsed}s ===", flush=True)
    print(f"  Z.AI scripts: {len(valid)}/{len(zai_models)}", flush=True)
    print(f"  Critiques: {sum(1 for v in m2.values() if v and not v.startswith('['))}/{len(di_critics)}", flush=True)
    print(f"  Refined: {len(valid3)}/{len(zai_models)}", flush=True)
    print(f"  TTS: {m4_count}", flush=True)
    print(f"  Images: {m5_count}", flush=True)
    print(f"  Embeddings: {len(m6)}", flush=True)
    print(f"  ASR: {len(m7)}", flush=True)
    print(f"  Files: {index['file_count']}", flush=True)


if __name__ == '__main__':
    main()
