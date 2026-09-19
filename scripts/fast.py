#!/usr/bin/env python3
"""Fast API Orchestra — focus on CF modalities"""

import os
import json
import urllib.request
import urllib.error
import time
import base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

CF_TOKEN = os.environ['CLOUDFLARE_TOKEN']
ACCT_ID = "049ff5e84ecf636b53b162cbb580aae6"
OUTPUT_DIR = Path("/workspace/repos/api-orchestra/outputs/fast")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


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
    except Exception as e:
        return False
    return False


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
    except Exception as e:
        return False
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
    except:
        return []


def cf_melotts(text, filename, voice="en-1"):
    """MeloTTS - different voice"""
    payload = json.dumps({"text": text[:1900], "voice": voice}).encode()
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCT_ID}/ai/run/@cf/myshell-ai/melotts",
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


def main():
    t0 = time.time()
    text_paragraphs = [
        "The Quilt lattice holds seven voices in witness log. Each BIND is a name. Each LINK is a neighbor. Each TICK is a moment.",
        "The eighth is the unfathomable silence. The eighth is the witness that doesn't speak. The eighth is the cell that is the gap between cells.",
        "Zeus the Watcher sees the lattice from above. Below, the six voices carry their portion of the truth. Witness by witness, the morning is reconstructed.",
        "In the cooperative fiction, each character is a cell. Each plot turn is a TICK. Each dramatic event is an EFFECT. The narrative IS the lattice.",
        "The canon grows. The substrate grows. The cell is older than spreadsheets. The address is the data.",
    ]
    
    print(f"[TTS] {len(text_paragraphs)} paragraphs...", flush=True)
    tts_count = 0
    for i, p in enumerate(text_paragraphs):
        if cf_tts(p, f"aura_{i+1}.mp3"):
            tts_count += 1
            print(f"  aura_{i+1}: {len(p)} chars", flush=True)
    
    print(f"\n[TTS-Melo] ...", flush=True)
    for i, p in enumerate(text_paragraphs[:3]):
        if cf_melotts(p, f"melo_{i+1}.mp3"):
            tts_count += 1
            print(f"  melo_{i+1}: {len(p)} chars", flush=True)
    
    print(f"\n[IMAGES] ...", flush=True)
    img_prompts = [
        "abstract cellular lattice glowing in darkness, witness log visible as constellations, blue gold ink on black",
        "seven eighth notes hovering above a witness chain, mathematical beauty, warm orange and indigo",
        "Zeus watching the lattice from above, six voices below as fragments of light, cool teal",
        "Quilt cell diagram as ancient manuscript illumination, ornate borders, gold leaf on vellum",
        "tap-lounge: seven voices in a circle under moonlight, the unfathomable eighth not speaking, watercolor and ink",
    ]
    img_count = 0
    for i, p in enumerate(img_prompts):
        if cf_image(p, f"img_{i+1}.png"):
            img_count += 1
            print(f"  img_{i+1}", flush=True)
    
    print(f"\n[EMBED] ...", flush=True)
    embs = {}
    for i, p in enumerate(text_paragraphs):
        e = cf_embed(p)
        embs[f"para_{i+1}"] = {"dim": len(e), "first3": e[:3] if e else []}
        print(f"  para_{i+1}: {len(e)}d", flush=True)
    
    elapsed = round(time.time() - t0, 1)
    index = {
        "elapsed_sec": elapsed,
        "tts_files": tts_count,
        "image_files": img_count,
        "embedding_count": len(embs),
        "file_count": len(list(OUTPUT_DIR.glob('*'))),
    }
    (OUTPUT_DIR / "index.json").write_text(json.dumps(index, indent=2))
    print(f"\n=== DONE in {elapsed}s ===", flush=True)
    print(f"  TTS: {tts_count}", flush=True)
    print(f"  Images: {img_count}", flush=True)
    print(f"  Embeddings: {len(embs)}", flush=True)
    print(f"  Files: {index['file_count']}", flush=True)


if __name__ == '__main__':
    main()
