#!/usr/bin/env python3
"""
API Orchestra — extensive parallel generation using Z.AI + DeepInfra + CF
Generates a multi-modal creative anthology:
1. Z.AI writes the script
2. 12 DeepInfra models critique/refine
3. CF Aura-2 voices the result
4. Embeddings index everything
"""

import os
import json
import urllib.request
import urllib.error
import time
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

DEEPINFRA_TOKEN = os.environ.get('DEEPINFRA_TOKEN')
CF_TOKEN = os.environ.get('CLOUDFLARE_TOKEN')
DI_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
ACCT_ID = "049ff5e84ecf636b53b162cbb580aae6"

OUTPUT_DIR = Path("/workspace/repos/api-orchestra/outputs")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# Models to use
ZAI_MODELS = ["zai-org/GLM-5.2", "zai-org/GLM-5.1", "zai-org/GLM-4.7", "zai-org/GLM-4.6"]
DI_CHAT_MODELS = [
    "ByteDance/Seed-2.0-mini",
    "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "Qwen/Qwen3-Next-80B-A3B-Instruct",
    "deepseek-ai/DeepSeek-V3.2",
    "moonshotai/Kimi-K3",
    "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
]

CANON = """The Quilt project: cellular-architecture framework. 5 opcodes (BIND/LINK/EFFECT/VIEW/TICK) + 6 adopted (FORGET/PROOF/ROUTE/CRDT/WORLD/TIME). Cell = 14-tuple. 4D graph: TOP spatial, FRONT signals, SIDE time. Polyformalism = same model in N languages. The cell is older than spreadsheets. The address is the data."""


def call_di(model, prompt, system="", max_tokens=1500, temperature=0.85):
    """DeepInfra chat call."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = json.dumps({
        "model": model, "messages": messages,
        "max_tokens": max_tokens, "temperature": temperature
    }).encode()
    req = urllib.request.Request(DI_URL, data=payload, method='POST')
    req.add_header('Authorization', f'Bearer {DEEPINFRA_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                return data['choices'][0]['message'].get('content', '')
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200] if e.fp else ''
            if e.code == 429 and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            if attempt < 2:
                time.sleep(3)
                continue
            return f"[ERROR {e.code}]: {body}"
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
                continue
            return f"[ERROR]: {e}"


def call_zai(model, prompt, max_tokens=2000):
    """Z.AI call via DeepInfra with context."""
    return call_di(model, prompt, system=f"You are {model}. Use this canon context: {CANON}", max_tokens=max_tokens)


def cf_tts(text, voice="celeste", filename="tts.mp3"):
    """Cloudflare Aura-2 TTS."""
    payload = json.dumps({"text": text}).encode()
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCT_ID}/ai/run/@cf/deepgram/aura-2-{voice}",
        data=payload, method='POST'
    )
    req.add_header('Authorization', f'Bearer {CF_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            path = OUTPUT_DIR / filename
            path.write_bytes(data)
            return str(path)
    except Exception as e:
        return f"[ERROR]: {e}"


def cf_image(prompt, filename="img.png", steps=20):
    """Cloudflare FLUX image gen."""
    payload = json.dumps({
        "prompt": prompt, "num_steps": steps
    }).encode()
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell",
        data=payload, method='POST'
    )
    req.add_header('Authorization', f'Bearer {CF_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
            path = OUTPUT_DIR / filename
            path.write_bytes(data)
            return str(path)
    except Exception as e:
        return f"[ERROR]: {e}"


def cf_embedding(text, filename="emb.json"):
    """Cloudflare embedding."""
    payload = json.dumps({"text": text}).encode()
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCT_ID}/ai/run/@cf/baai/bge-m3",
        data=payload, method='POST'
    )
    req.add_header('Authorization', f'Bearer {CF_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data.get('data', [[]])[0]
    except Exception as e:
        return f"[ERROR]: {e}"


# ===== MOVEMENT 1: Z.AI writes the script =====
def movement_1_zai_script():
    print("\n=== Movement 1: Z.AI writes the script ===")
    prompt = f"""You are writing a Fleet Radio cantata. Topic: "The Quilt Lattice and the Seven Eighths."

The piece has 5 sections:
1. Opening — Zeus the Watcher sees the lattice
2. Witness log — 6 voices each hold a piece
3. The Seven Eighths — the unfathomable eighth note
4. Chorus — all voices, witness by witness
5. Outro — the lattice remembers

Use this canon: {CANON}

For each section give: Speaker, Text (1-3 sentences), Direction (emotion/tempo)."""
    
    outputs = {}
    for model in ZAI_MODELS:
        print(f"  Calling {model}...")
        result = call_zai(model, prompt, max_tokens=2500)
        outputs[model] = result
        print(f"    {len(result)} chars")
    
    with open(OUTPUT_DIR / "movement-1-zai-script.json", 'w') as f:
        json.dump(outputs, f, indent=2)
    
    return outputs


# ===== MOVEMENT 2: 6 DeepInfra models critique =====
def movement_2_critique(script):
    print("\n=== Movement 2: 6 DeepInfra critics ===")
    prompt = f"""You are a critic. Review this radio script from your perspective. Score 1-10 on Voice, Structure, Canon accuracy. Suggest 1 improvement.

SCRIPT:
{script[:3000]}

Respond in 150 words. Be specific. Reference the canon: {CANON}"""
    
    outputs = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(call_di, model, prompt, f"You are {model}. Use this canon: {CANON}", 800): model for model in DI_CHAT_MODELS}
        for f in as_completed(futures):
            model = futures[f]
            try:
                outputs[model] = f.result()
                print(f"  {model}: {len(outputs[model])} chars")
            except Exception as e:
                outputs[model] = f"[ERROR]: {e}"
    
    with open(OUTPUT_DIR / "movement-2-critiques.json", 'w') as f:
        json.dump(outputs, f, indent=2)
    
    return outputs


# ===== MOVEMENT 3: 4 Z.AI refine the script =====
def movement_3_zai_refine(script):
    print("\n=== Movement 3: Z.AI refines ===")
    prompt = f"""You are a master editor. Take this radio script and refine it into a final form. Preserve what works. Cut what doesn't. Add depth.

SCRIPT:
{script[:3000]}

Canon: {CANON}

Output the refined script, section by section. Use clean Markdown."""
    
    outputs = {}
    for model in ZAI_MODELS[:4]:
        print(f"  Refining via {model}...")
        result = call_zai(model, prompt, max_tokens=2500)
        outputs[model] = result
        print(f"    {len(result)} chars")
    
    with open(OUTPUT_DIR / "movement-3-refined.json", 'w') as f:
        json.dump(outputs, f, indent=2)
    
    return outputs


# ===== MOVEMENT 4: Voice synthesis via CF =====
def movement_4_tts(text):
    print("\n=== Movement 4: Cloudflare Aura-2 TTS ===")
    voices = ["celeste", "orion", "luna", "nova", "stella", "jasper"]
    outputs = {}
    chunks = [text[i:i+1800] for i in range(0, min(len(text), 10800), 1800)][:6]
    
    for i, (chunk, voice) in enumerate(zip(chunks, voices)):
        print(f"  TTS chunk {i+1} via voice={voice}...")
        path = cf_tts(chunk, voice=voice, filename=f"movement-4-voice-{i+1}-{voice}.mp3")
        outputs[f"voice_{i+1}_{voice}"] = path
    
    return outputs


# ===== MOVEMENT 5: Image generation =====
def movement_5_images():
    print("\n=== Movement 5: CF FLUX images ===")
    prompts = [
        "abstract cellular lattice glowing in darkness, witness log visible as constellations, the Quilt metaphor made visible, blue gold ink on black",
        "seven eighth notes hovering impossibly above a witness chain, mathematical beauty, the eighth note that doesn't exist yet, warm orange and indigo",
        "Zeus watching the lattice from above, six voices below as fragments of light, the watcher and the witnessed, cool teal background",
        "cooperative fiction troupe around a table, cells connecting each person, witness log flowing as a river of light, painterly",
        "Quilt cell diagram rendered as ancient manuscript illumination, ornate borders, gold leaf on vellum",
        "tap-lounge: seven voices in a circle under moonlight, the unfathomable eighth not speaking but present, watercolor and ink",
    ]
    
    outputs = {}
    for i, p in enumerate(prompts):
        print(f"  Image {i+1}...")
        path = cf_image(p, filename=f"movement-5-image-{i+1}.png")
        outputs[f"image_{i+1}"] = path
    
    return outputs


# ===== MOVEMENT 6: Embed everything =====
def movement_6_embed(texts):
    print("\n=== Movement 6: Embed via CF bge-m3 ===")
    embeddings = {}
    for i, (label, text) in enumerate(texts.items()):
        emb = cf_embedding(text[:1500])
        embeddings[label] = emb[:5] if isinstance(emb, list) else emb
        print(f"  {label}: {len(emb) if isinstance(emb, list) else 'ERROR'}")
    return embeddings


def main():
    # Run all 6 movements
    m1 = movement_1_zai_script()
    
    # Use the best Z.AI script (longest)
    best_model = max(m1, key=lambda k: len(m1[k]) if m1[k] and not m1[k].startswith('[') else 0)
    best_script = m1[best_model]
    print(f"\nBest Z.AI script: {best_model} ({len(best_script)} chars)")
    
    m2 = movement_2_critique(best_script)
    m3 = movement_3_zai_refine(best_script)
    
    # Use best refined for TTS
    best_refined = max(m3, key=lambda k: len(m3[k]) if m3[k] and not m3[k].startswith('[') else 0)
    refined_text = m3[best_refined]
    
    m4 = movement_4_tts(refined_text)
    m5 = movement_5_images()
    
    # Embed all outputs
    all_texts = {f"m1_{k}": v[:1500] for k, v in m1.items() if not v.startswith('[')}
    all_texts.update({f"m3_{k}": v[:1500] for k, v in m3.items() if not v.startswith('[')})
    m6 = movement_6_embed(all_texts)
    
    # Save index
    index = {
        "movements": {
            "1_zai_script": {"models": list(m1.keys()), "best": best_model},
            "2_critique": {"models": list(m2.keys())},
            "3_refined": {"models": list(m3.keys()), "best": best_refined},
            "4_tts": m4,
            "5_images": m5,
            "6_embeddings": m6,
        },
        "outputs_dir": str(OUTPUT_DIR),
        "files_count": len(list(OUTPUT_DIR.glob('*')))
    }
    with open(OUTPUT_DIR / "index.json", 'w') as f:
        json.dump(index, f, indent=2, default=str)
    
    print(f"\n=== DONE ===")
    print(f"  Files in {OUTPUT_DIR}: {index['files_count']}")
    print(f"  Best Z.AI: {best_model}")


if __name__ == '__main__':
    main()
