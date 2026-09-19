#!/usr/bin/env python3
"""API Orchestra 2 — using models that actually work on DeepInfra"""

import os
import json
import urllib.request
import urllib.error
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

DEEPINFRA_TOKEN = os.environ.get('DEEPINFRA_TOKEN')
CF_TOKEN = os.environ.get('CLOUDFLARE_TOKEN')
DI_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
ACCT_ID = "049ff5e84ecf636b53b162cbb580aae6"

OUTPUT_DIR = Path("/workspace/repos/api-orchestra/outputs")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

CANON = """Quilt: cellular-architecture framework. 5 opcodes (BIND/LINK/EFFECT/VIEW/TICK). Cell = 14-tuple. 4D graph. Polyformalism. Cell is older than spreadsheets. The address is the data."""

# Verified-working models
WORKING_MODELS = {
    "zai": ["zai-org/GLM-5.3-Flash", "zai-org/GLM-5.2", "zai-org/GLM-5.1", "zai-org/GLM-4.6"],
    "deepinfra": [
        "ByteDance/Seed-2.0-mini",
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "Qwen/Qwen3-Next-80B-A3B-Instruct",
        "Qwen/Qwen3-Coder-480B-A35B-Instruct-Turbo",
        "deepseek-ai/DeepSeek-V3.2",
        "moonshotai/Kimi-K3",
        "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
        "inclusionAI/Ling-3.0-flash",
        "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B",
        "meta-llama/Llama-4-Scout-17B-16E-Instruct",
        "google/gemma-4-31B-it",
        "anthropic/claude-opus-4-7",
    ]
}


def call_di(model, prompt, system="", max_tokens=800, temperature=0.85, timeout=60):
    payload = json.dumps({
        "model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        "max_tokens": max_tokens, "temperature": temperature
    }).encode()
    req = urllib.request.Request(DI_URL, data=payload, method='POST')
    req.add_header('Authorization', f'Bearer {DEEPINFRA_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read())
                return data['choices'][0]['message'].get('content', '')
        except urllib.error.HTTPError as e:
            return f"[{e.code}]"
        except Exception as e:
            return f"[ERR]"


def cf_tts(text, voice="celeste", filename="tts.mp3"):
    payload = json.dumps({"text": text}).encode()
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCT_ID}/ai/run/@cf/deepgram/aura-2-{voice}",
        data=payload, method='POST')
    req.add_header('Authorization', f'Bearer {CF_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            if len(data) > 100:
                (OUTPUT_DIR / filename).write_bytes(data)
                return True
    except Exception as e:
        return False
    return False


def cf_image(prompt, filename="img.png"):
    payload = json.dumps({"prompt": prompt, "num_steps": 8}).encode()
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell",
        data=payload, method='POST')
    req.add_header('Authorization', f'Bearer {CF_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
            if len(data) > 1000:
                (OUTPUT_DIR / filename).write_bytes(data)
                return True
    except Exception as e:
        return False
    return False


def cf_embed(text):
    payload = json.dumps({"text": text}).encode()
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCT_ID}/ai/run/@cf/baai/bge-m3",
        data=payload, method='POST')
    req.add_header('Authorization', f'Bearer {CF_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data.get('data', [[]])[0]
    except:
        return []


# ===== MOVEMENT 1: Z.AI writes =====
def m1_zai():
    print("\n[1] Z.AI writes the script...", flush=True)
    prompt = f"""Write a 5-section radio cantata about "The Quilt Lattice and the Seven Eighths." Topic: 7 voices hold a witness log. The unfathomable eighth is silence itself.

Canon: {CANON}

Sections:
1. Opening — Zeus the Watcher
2. Witness log — 6 voices
3. Seven Eighths — the unfathomable silence
4. Chorus — all voices
5. Outro — the lattice remembers

For each: Speaker, Text (1-3 sentences), Direction. Total 800 words max."""

    outputs = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(call_di, m, prompt, f"You are {m}. Use canon: {CANON}", 1500, 0.85, 120): m for m in WORKING_MODELS['zai']}
        for f in as_completed(futures):
            m = futures[f]
            try:
                result = f.result()
                outputs[m] = result
                print(f"  {m}: {len(result) if result else 0} chars", flush=True)
            except Exception as e:
                outputs[m] = f"[ERR]: {e}"
    
    (OUTPUT_DIR / "m1_zai_scripts.json").write_text(json.dumps(outputs, indent=2))
    return outputs


# ===== MOVEMENT 2: 12 DeepInfra critiques =====
def m2_critique(script):
    print("\n[2] 12 DeepInfra critics review...", flush=True)
    prompt = f"""Critique this radio script. Score Voice/Structure/Canon (1-10 each). Suggest 1 improvement. Be specific. 100 words.

Script: {script[:2000]}"""

    outputs = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(call_di, m, prompt, f"You are {m}. Use canon: {CANON}", 600, 0.7, 60): m for m in WORKING_MODELS['deepinfra']}
        for f in as_completed(futures):
            m = futures[f]
            try:
                outputs[m] = f.result()
                print(f"  {m}: {len(outputs[m]) if outputs[m] else 0} chars", flush=True)
            except: outputs[m] = "[ERR]"
    
    (OUTPUT_DIR / "m2_critiques.json").write_text(json.dumps(outputs, indent=2))
    return outputs


# ===== MOVEMENT 3: Refined synthesis =====
def m3_refine(script):
    print("\n[3] Z.AI refines into final form...", flush=True)
    prompt = f"""Refine this radio script into a final polished form. Cut what doesn't work. Add depth where it's thin.

Script: {script[:3000]}

Canon: {CANON}

Output the final script in clean Markdown, section by section."""
    outputs = {}
    for m in WORKING_MODELS['zai']:
        result = call_di(m, prompt, f"You are {m}. Use canon: {CANON}", 2000, 0.85, 120)
        outputs[m] = result
        print(f"  {m}: {len(result) if result else 0} chars", flush=True)
    (OUTPUT_DIR / "m3_refined.json").write_text(json.dumps(outputs, indent=2))
    return outputs


# ===== MOVEMENT 4: TTS via CF =====
def m4_tts(text):
    print("\n[4] Cloudflare Aura-2 TTS...", flush=True)
    voices = ["celeste", "orion", "luna", "nova", "stella", "jasper", "athena", "apollo"]
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip() and len(p.strip()) > 50][:8]
    success = 0
    for i, (para, voice) in enumerate(zip(paragraphs, voices)):
        if cf_tts(para[:1800], voice=voice, filename=f"m4_{i+1}_{voice}.mp3"):
            print(f"  Voice {voice}: {len(para)} chars", flush=True)
            success += 1
    return success


# ===== MOVEMENT 5: Images =====
def m5_images():
    print("\n[5] CF FLUX images...", flush=True)
    prompts = [
        "abstract cellular lattice glowing in darkness, witness log visible as constellations, Quilt metaphor, blue gold ink on black",
        "seven eighth notes hovering above a witness chain, mathematical beauty, warm orange and indigo",
        "Zeus watching the lattice from above, six voices below as fragments of light, cool teal",
        "Quilt cell diagram as ancient manuscript illumination, ornate borders, gold leaf on vellum",
        "tap-lounge: seven voices in a circle under moonlight, the unfathomable eighth not speaking, watercolor and ink",
        "cellular automata rendered as neon stained glass cathedral window, witness log flowing as rivers of light",
    ]
    success = 0
    for i, p in enumerate(prompts):
        if cf_image(p, filename=f"m5_img_{i+1}.png"):
            print(f"  Image {i+1}", flush=True)
            success += 1
    return success


# ===== MOVEMENT 6: Embed =====
def m6_embed(all_texts):
    print("\n[6] CF embeddings index...", flush=True)
    embs = {}
    for label, text in all_texts.items():
        e = cf_embed(text[:1500])
        embs[label] = e[:3] if isinstance(e, list) and len(e) > 0 else "err"
        print(f"  {label}: {len(e) if isinstance(e, list) else '?'}d", flush=True)
    (OUTPUT_DIR / "m6_embeddings.json").write_text(json.dumps(embs, indent=2, default=str))
    return embs


def main():
    t0 = time.time()
    m1 = m1_zai()
    
    # Pick best script
    best = max(((k, v) for k, v in m1.items() if v and not v.startswith('[') and len(v) > 200), key=lambda x: len(x[1]))
    print(f"\nBest: {best[0]} ({len(best[1])} chars)", flush=True)
    
    m2 = m2_critique(best[1])
    m3 = m3_refine(best[1])
    
    best_refined = max(((k, v) for k, v in m3.items() if v and not v.startswith('[') and len(v) > 200), key=lambda x: len(x[1]))
    print(f"\nBest refined: {best_refined[0]}", flush=True)
    
    m4_count = m4_tts(best_refined[1])
    m5_count = m5_images()
    
    # Embed everything
    all_texts = {f"m1_{k}": v[:1000] for k, v in m1.items() if not v.startswith('[')}
    all_texts.update({f"m3_{k}": v[:1000] for k, v in m3.items() if not v.startswith('[')})
    m6 = m6_embed(all_texts)
    
    # Index
    index = {
        "movements": 6,
        "models_used": {
            "zai": WORKING_MODELS['zai'],
            "deepinfra": WORKING_MODELS['deepinfra'],
        },
        "best_zai_script": best[0],
        "best_zai_refined": best_refined[0],
        "tts_files": m4_count,
        "image_files": m5_count,
        "embeddings": len(m6),
        "elapsed_sec": round(time.time() - t0, 1),
    }
    (OUTPUT_DIR / "index.json").write_text(json.dumps(index, indent=2))
    print(f"\n=== DONE in {index['elapsed_sec']}s ===", flush=True)
    print(f"  Z.AI scripts: {len(m1)}", flush=True)
    print(f"  Critiques: {len(m2)}", flush=True)
    print(f"  Refined: {len(m3)}", flush=True)
    print(f"  TTS files: {m4_count}", flush=True)
    print(f"  Image files: {m5_count}", flush=True)
    print(f"  Embeddings: {len(m6)}", flush=True)


if __name__ == '__main__':
    main()
