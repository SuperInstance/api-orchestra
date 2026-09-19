#!/usr/bin/env python3
"""
DeepInfra Ideators — brainstorm the shape of future repos we can't yet name
Uses 30+ models from 14 vendors as different "ideator personalities"
Each one invents 1-3 repo concepts that we don't have yet
"""

import os, json, urllib.request, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

DEEPINFRA_TOKEN = os.environ.get('DEEPINFRA_TOKEN')
DI_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
OUTPUT_DIR = Path("/workspace/repos/api-orchestra/outputs/ideator_brainstorm")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

CANON = """Quilt: cellular-architecture framework. 5 opcodes (BIND/LINK/EFFECT/VIEW/TICK). Cell = 14-tuple. 4D graph. Polyformalism. Cell is older than spreadsheets. The address is the data."""

# Ideator personalities — each model gets a unique role to ideate from
IDEATORS = [
    # Z.AI family — Chinese-trained models
    ("zai-org/GLM-5.3-Flash", "Eastern systems thinker", "You see cells as rice paddies, irrigation networks, family lineages. What repo would Quilt need that doesn't exist?"),
    
    # ByteDance — Chinese creative + multimodal
    ("ByteDance/Seed-2.0-mini", "ByteDance creative director", "You see cells as viral content loops, recommendation cascades, attention economies. What repo would Quilt need?"),
    
    # Meta — Western foundation model
    ("meta-llama/Llama-3.3-70B-Instruct-Turbo", "Open-source philosopher", "You see cells as commons, gift economies, community libraries. What repo would Quilt need that respects the commons?"),
    ("meta-llama/Llama-4-Scout-17B-16E-Instruct", "MoE architect", "You see cells as routed specialists. What repo would Quilt need that exploits sparse routing?"),
    
    # Qwen — Alibaba
    ("Qwen/Qwen3-Next-80B-A3B-Instruct", "Multilingual diplomat", "You see cells as international treaties, translation pipelines. What repo would Quilt need that crosses language boundaries?"),
    ("Qwen/Qwen3-Coder-480B-A35B-Instruct-Turbo", "Code-as-poetry advocate", "You see cells as functions, signatures, type theory. What repo would Quilt need that's actually a programming language?"),
    
    # DeepSeek family
    ("deepseek-ai/DeepSeek-V4-Flash", "Rapid worldbuilder", "You see cells as starting states and presets. Loop with yourself: generate 3 starting states for a Quilt repo that doesn't exist yet. The starting state matters more than the destination."),
    ("deepseek-ai/DeepSeek-V3.2", "Reasoning explorer", "You see cells as logic gates, proof trees, verification chains. What repo would Quilt need that's actually a theorem prover?"),
    ("deepseek-ai/DeepSeek-R1-0528", "Deep reasoner", "You see cells as scars, traumas, healing. What repo would Quilt need that holds emotional truth?"),
    
    # Kimi — Moonshot
    ("moonshotai/Kimi-K3", "Long-context storyteller", "You see cells as memories, narratives, dreams. What repo would Quilt need that holds a 100,000-page canon?"),
    ("moonshotai/Kimi-K2.7-Code", "Code archaeologist", "You see cells as COBOL, Fortran, ancient languages. What repo would Quilt need that bridges to legacy systems?"),
    
    # Mistral — French
    ("mistralai/Mistral-Small-3.2-24B-Instruct-2506", "Revolutionary romantic", "You see cells as liberté, égalité, fraternité. What repo would Quilt need that's actually a revolution?"),
    
    # Inclusion AI — Asian multilinguality
    ("inclusionAI/Ling-3.0-flash", "Pacific Rim voice", "You see cells as trade winds, ocean currents, Pacific crossings. What repo would Quilt need that sails?"),
    
    # NVIDIA — engineering
    ("nvidia/NVIDIA-Nemotron-3-Super-120B-A12B", "MoE engineer", "You see cells as parallel threads, GPU warps, sparse activations. What repo would Quilt need that runs at 100x?"),
    ("nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B", "Sparse architect", "You see cells as conditional computation. What repo would Quilt need that uses 99% of params 1% of the time?"),
    
    # Anthropic — alignment
    ("anthropic/claude-opus-4-7", "Constitutional AI", "You see cells as principles, values, rights. What repo would Quilt need that encodes its constitution?"),
    
    # Google — research
    ("google/gemma-4-31B-it", "DeepMind researcher", "You see cells as neural activations, attention heads, layer-wise representations. What repo would Quilt need that bridges to neural nets?"),
    ("google/gemma-3-27b-it", "Google scale engineer", "You see cells as Spanner, Bigtable, MapReduce. What repo would Quilt need that scales to billions?"),
    
    # Microsoft
    ("microsoft/phi-4", "Compact philosopher", "You see cells as small truths, dense knowledge. What repo would Quilt need that fits in 14B params?"),
    
    # OpenAI
    ("openai/gpt-oss-120b", "OSS advocate", "You see cells as open weights, transparent architectures. What repo would Quilt need that anyone can fork?"),
    ("openai/gpt-oss-20b", "Lightweight OSS", "You see cells as efficient inference, edge deployment. What repo would Quilt need that runs on a phone?"),
    
    # Others
    ("MiniMaxAI/MiniMax-M3", "Max's sibling", "You see cells as MiniMax models, scaling laws, emergent capabilities. What repo would Quilt need that emerges?"),
    ("MiniMaxAI/MiniMax-M2.7-Turbo", "Turbo speedrunner", "You see cells as fast paths, optimized routes. What repo would Quilt need that ships in 1 hour?"),
    
    # Meta 70B
    ("meta-llama/Meta-Llama-3.1-70B-Instruct", "Pure 70B", "You see cells as Llama-style transformer layers. What repo would Quilt need that re-derives from first principles?"),
    ("meta-llama/Meta-Llama-3.1-8B-Instruct", "Small but mighty", "You see cells as compact reasoning. What repo would Quilt need that runs in 8B?"),
    
    # Qwen 32B
    ("Qwen/Qwen3-32B", "Mid-size Qwen", "You see cells as mid-scale balance. What repo would Quilt need that's neither too big nor too small?"),
    
    # DeepSeek V3
    ("deepseek-ai/DeepSeek-V3", "V3 base", "You see cells as MoE architectures. What repo would Quilt need that's MoE-native?"),
    
    # Step
    ("stepfun-ai/Step-3.7-Flash", "Step fun creative", "You see cells as dance steps, music beats, game turns. What repo would Quilt need that has rhythm?"),
]


def call(model, prompt, system="", max_tokens=1200, temperature=0.85, timeout=45):
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


def main():
    t0 = time.time()
    
    # Round 1: 30 ideators each name 1 repo
    print(f"\n[ROUND 1] {len(IDEATORS)} ideators brainstorm repo names...", flush=True)
    
    def call_ideator(ideator):
        model, role, prompt = ideator
        # Special for DeepSeek-V4-Flash: have it loop with itself
        if 'DeepSeek-V4-Flash' in model:
            system = f"You are {role}. Canon: {CANON}"
            # First call: initial brainstorm
            r1 = call(model, f"{prompt}\n\nOutput: repo name + one-sentence description + key dials (3 sliders). 200 words max.", system, 800, 0.85)
            # Second call: refine
            r2 = call(model, f"From your previous answer: '{r1[:500]}'\n\nLoop with yourself. Find the novel dial — the slider that changes everything. 100 words.", system, 400, 0.85)
            # Third call: find what values matter
            r3 = call(model, f"Continue looping: what are the 3 values people would care about most in this repo? 100 words.", system, 400, 0.85)
            return model, role, {"initial": r1, "refined": r2, "values": r3}
        else:
            system = f"You are {role}. Canon: {CANON}"
            result = call(model, f"{prompt}\n\nOutput: repo name + one-sentence description + key dials (3 sliders). 200 words max.", system, 800, 0.85)
            return model, role, result
    
    r1 = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = [ex.submit(call_ideator, ideator) for ideator in IDEATORS]
        for f in as_completed(futures):
            try:
                model, role, result = f.result()
                r1[model] = {"role": role, "result": result}
                print(f"  {model}: {role[:30]}", flush=True)
            except Exception as e:
                print(f"  ERR: {e}", flush=True)
    (OUTPUT_DIR / "r1_30_ideators.json").write_text(json.dumps(r1, indent=2))
    
    # Round 2: Cross-pollination — 8 models combine pairs of repos
    print(f"\n[ROUND 2] Cross-pollination of repo ideas...", flush=True)
    r1_text = json.dumps(r1, indent=2)[:3500]
    xpoll_models = ["Qwen/Qwen3-Coder-480B-A35B-Instruct-Turbo", "moonshotai/Kimi-K3", "deepseek-ai/DeepSeek-V4-Flash", "zai-org/GLM-5.3-Flash", "ByteDance/Seed-2.0-mini", "inclusionAI/Ling-3.0-flash", "anthropic/claude-opus-4-7", "meta-llama/Llama-3.3-70B-Instruct-Turbo"]
    
    xpoll_prompt = f"""Cross-pollinate 2 of these repo ideas into a new hybrid repo that doesn't exist.

Repo ideas: {r1_text}

Output: new repo name + what it does + which 2 it merged + key novel dial. 200 words."""
    
    r2 = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(call, m, xpoll_prompt, f"You are {m}. Canon: {CANON}", 700, 0.85, 45): m for m in xpoll_models}
        for f in as_completed(futures):
            m = futures[f]
            try:
                r2[m] = f.result()
                print(f"  {m}: {len(r2[m]) if r2[m] and not r2[m].startswith('[') else 'ERR'}", flush=True)
            except: r2[m] = "[ERR]"
    (OUTPUT_DIR / "r2_xpoll.json").write_text(json.dumps(r2, indent=2))
    
    # Round 3: DeepSeek V4-Flash loops with itself — 5 iterations on worldbuilding
    print(f"\n[ROUND 3] DeepSeek V4-Flash worldbuilding loop...", flush=True)
    v4flash = "deepseek-ai/DeepSeek-V4-Flash"
    
    iterations = []
    current_state = "A starting state: empty 5-cell lattice, all cells unbound. 3 sliders: density (0-1), urgency (0-1), depth (1-7). What values matter?"
    
    for i in range(5):
        prompt = f"""You're iterating with yourself. Previous state: '{current_state}'

Loop iteration {i+1}: 
- Generate a NEW starting state (specific values for all dials)
- Name 3 sliders that matter most in this state
- Find one NOVEL dial that doesn't exist yet
- Identify what values people would care about

100 words max."""
        system = f"You are {v4flash}. Canon: {CANON}. Worldbuilding: starting states and presets matter more than destinations. You're looping with yourself to find where novel dials should be by seeing many different routes work."
        
        result = call(v4flash, prompt, system, 600, 0.85, 30)
        iterations.append({"iteration": i+1, "input": current_state[:300], "output": result})
        current_state = result[:300]
        print(f"  iter {i+1}: {len(result)} chars", flush=True)
        # Don't loop too fast
        time.sleep(0.2)
    
    (OUTPUT_DIR / "r3_v4_flash_loop.json").write_text(json.dumps(iterations, indent=2))
    
    # Round 4: Synthesize all 30 ideators into a "future of Quilt" document
    print(f"\n[ROUND 4] Synthesizing future-of-Quilt...", flush=True)
    all_text = json.dumps({"r1": r1, "r2": r2, "r3": iterations}, indent=2)[:5000]
    synth_models = ["zai-org/GLM-5.3-Flash", "deepseek-ai/DeepSeek-V4-Flash", "Qwen/Qwen3-Coder-480B-A35B-Instruct-Turbo", "moonshotai/Kimi-K3"]
    
    synth_prompt = f"""Synthesize all these brainstormed repo ideas into a 'Future of Quilt' document.

Material: {all_text}

Canon: {CANON}

Output: 
1. 5 most novel repos that don't exist yet
2. 3 cross-cutting themes
3. 1 surprising insight about where Quilt is going

500 words max."""
    
    r4 = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(call, m, synth_prompt, f"You are {m}. Canon: {CANON}", 1200, 0.85, 45): m for m in synth_models}
        for f in as_completed(futures):
            m = futures[f]
            try:
                r4[m] = f.result()
                print(f"  {m}: {len(r4[m]) if r4[m] and not r4[m].startswith('[') else 'ERR'}", flush=True)
            except: r4[m] = "[ERR]"
    (OUTPUT_DIR / "r4_synthesis.json").write_text(json.dumps(r4, indent=2))
    
    elapsed = round(time.time() - t0, 1)
    index = {
        "rounds": 4,
        "ideators": len(IDEATORS),
        "r1_results": sum(1 for v in r1.values() if isinstance(v.get('result'), str) and not v['result'].startswith('[')) + sum(1 for v in r1.values() if isinstance(v.get('result'), dict) and v['result'].get('initial', '').strip()),
        "r2_xpoll": sum(1 for v in r2.values() if v and not v.startswith('[')),
        "r3_iterations": len(iterations),
        "r4_synthesis": sum(1 for v in r4.values() if v and not v.startswith('[')),
        "elapsed_sec": elapsed,
        "file_count": len(list(OUTPUT_DIR.glob('*'))),
    }
    (OUTPUT_DIR / "index.json").write_text(json.dumps(index, indent=2))
    
    print(f"\n=== DONE in {elapsed}s ===", flush=True)
    print(f"  R1 ideators: {index['r1_results']}/{len(IDEATORS)}", flush=True)
    print(f"  R2 xpoll: {index['r2_xpoll']}/8", flush=True)
    print(f"  R3 v4-flash iterations: {index['r3_iterations']}", flush=True)
    print(f"  R4 synthesis: {index['r4_synthesis']}/4", flush=True)
    print(f"  Files: {index['file_count']}", flush=True)


if __name__ == '__main__':
    main()
