# API Orchestra — Using every API, every model

**In plain terms:** this repo is a multi-LLM chorus. Instead of asking one model to write something and trusting the answer, it asks several models at once — a Z.AI draft, then a chord of ~12 critic models from different vendors, then a refine pass — and promotes the output that survives the disagreement to "canon." The canon is then pushed through non-LLM substrates (Cloudflare text-to-speech, image generation, embeddings, speech-to-text) to test whether the same shape survives the round trip. Everything is plain-`urllib` Python — no SDKs, no framework — and a full run costs about $0.10.

A creative anthology built by orchestrating **6+ Z.AI models, 12+ DeepInfra critics, Cloudflare AI's TTS/embedding/ASR/image stack, and async Python subagents** in parallel — until the result is canon.

The point isn't to advertise how many models can be touched. The point is that **single-model generation has structural blind spots** that only become visible when N models say things differently. The orchestra finds the canon-shaped description by exhausting the disagreement.

---

## What's in here

```
api-orchestra/
├── README.md              (this file)
├── scripts/               (all runners live here — run them from this dir)
│   ├── orchestra2.py        (multi-LLM DeepInfra script → 12 critics → refine)
│   ├── orchestra3.py        (adds Cloudflare TTS + image gen + ASR round-trip)
│   ├── extensive.py         (ZAI + 12 DeepInfra critics, 50+ parallel calls)
│   ├── fast.py              (Cloudflare modalities only — TTS/image/embed, sub-2-min)
│   ├── massive.py           (15-deep ideation across all providers in parallel)
│   ├── ideator_brainstorm.py(the ideator loop — 5 N-of-M waves, 30+ model personalities)
│   └── orchestrate.py       (full LLM orchestration variant — Z.AI + DeepInfra + CF pipeline)
├── outputs/               (everything produced — scripts, critiques, MP3s, PNGs)
├── *.log                  (one log per orchestration run)
└── outputs/index.json     (machine-readable summary of the last run)
```

Note: there is no `orchestra.py` — the original 7-move pipeline survives as
`scripts/orchestra3.py` (moves 1–7, including the ASR round-trip). The
`outputs/` tree also holds real artifacts from past runs (MP3s, PNGs,
per-run `index.json`) — see **Sample artifacts** below.

---

## The recipe — 7 movements

| Move | Inputs | Outputs | Models |
|------|--------|---------|--------|
| **1 — script draft** | topic + canon-context | 12-slot "movie script" | ZAI GLM-5.3-Flash, GLM-5.1, GLM-5.2, GLM-4.6 |
| **2 — critique chord** | the script | 12 critic reviews | DeepInfra Qwen3 / Llama-3.3 / DeepSeek-V3 / Kimi-K3 / Mistral / Ling / Nemotron / Llama-4 / Gemma-4 / Claude-Opus / ByteDance Seed-2.0 |
| **3 — refine pass** | script + critiques | canonical script | ZAI GLM refine (last run: GLM-4.6; the model that produced it is recorded) |
| **4 — voice** | canonical script | 6 MP3s | Cloudflare Aura-2 TTS (varied voices, varied tempos) |
| **5 — image** | canonical script + topics | 5 PNGs | Cloudflare FLUX-1-Schnell |
| **6 — embeddings** | canonical script | 7 vectors | Cloudflare BGE-M3 (768-dim) |
| **7 — ASR round-trip** | MP3s | transcribed JSON | Whisper (via DeepInfra) |

Each move builds on the previous. The final artifact is **the chord-confirmed canon** (move 3) plus its surface manifestations (audio + image + embedding + ASR verified).

---

## Doctrine: why this works

The three doctrines the API orchestra demonstrates:

1. **Three voices > one.** A single model has a structural blind spot for what it can't say. With 12 critics, the chord hears what each individual voice missed.

2. **Best-of-best as canonical.** After all critiques, ZAI re-drafts against the aggregated feedback. The refined output becomes the canonical version. The model that produced it is recorded.

3. **Cross-modal confirmation.** Moving from text → audio → image → embedding → transcription back to text tests each substrate's ability to carry the same canon-shape. If the ASR round-trip disagrees with the original script, the canon is wrong somewhere.

This is **canon-discovery in motion**: the opera *is* a witness log, and the witness is the chord.

---

## How to run

```bash
git clone https://github.com/SuperInstance/api-orchestra
cd api-orchestra/scripts

# Standard version (~7 min, 7 moves, full pipeline incl. ASR round-trip)
python3 orchestra3.py

# Maximum version (~10 min, 12 critics)
python3 extensive.py

# Ideator brainstorms (~3 min, 5 waves × N ideas)
python3 ideator_brainstorm.py

# Cheap modality pass (~2 min — Cloudflare TTS + image + embedding only,
# no script draft, no critics)
python3 fast.py
```

There are no CLI flags — the topic and prompts are hardcoded in each script.
Outputs land in `outputs/<runner>/`, and `orchestra3.py` rewrites
`outputs/index.json` with the run summary.

**Verified smoke check** (run 2026-09-28 against this exact tree):

```
$ python3 -m py_compile scripts/*.py     # all 7 runners compile clean
$ python3 scripts/fast.py                # without tokens, fails fast and honestly:
Traceback (most recent call last):
  File "scripts/fast.py", line 13, in <module>
    CF_TOKEN = os.environ['CLOUDFLARE_TOKEN']
KeyError: 'CLOUDFLARE_TOKEN'
```

**Required env**: `DEEPINFRA_TOKEN`, `CLOUDFLARE_TOKEN` — that's the whole list.
Z.AI models (GLM-*) are reached *through DeepInfra* (`zai-org/*` model IDs), so
there is no separate `ZAI_TOKEN`. **Gotcha**: every script hardcodes
`OUTPUT_DIR = /workspace/repos/api-orchestra/outputs/...`; on any other machine
either create that path or edit the constant.

**What a real run looks like** (from the checked-in `orchestra.log`):

```
[1] Z.AI writes the script...
  zai-org/GLM-5.2: 2152 chars
  zai-org/GLM-5.3-Flash: 4599 chars
Best: zai-org/GLM-5.3-Flash (4599 chars)
[2] 12 DeepInfra critics review...
  Qwen/Qwen3-Next-80B-A3B-Instruct: 558 chars
  ...
```

Each run writes outputs to `outputs/<run-stamp>/` and updates `index.json` with the summary.

---

## Empirical results from the last full run

| Stage | Best pick | Wall-time |
|-------|-----------|-----------|
| Script | ZAI GLM-5.3-Flash (4347 chars) | ~32s |
| Critiques | 12 DeepInfra models in parallel | ~85s |
| Refined script | ZAI GLM-4.6 | ~28s |
| 6 TTS outputs | Aura-2 voices | ~95s |
| 5 image outputs | FLUX-1-Schnell | ~62s |
| 7 embeddings | BGE-M3 | ~6s |
| 3 ASR round-trips | Whisper | ~52s |
| **Total** | — | **~7.2 min** |

12 critics × 600 tokens ≈ 7,200 input tokens per move. ~50K tokens total per full run. At ~$1.50/M input + $0.50/M output = **~$0.10 per full orchestra run**. This is the canonical cost profile for the multi-LLM chord.

---

## Sample artifacts (checked into `outputs/`)

Real output from past runs — what "canon + surface manifestations" actually looks like:

- `outputs/m5_img_*.png` — 5 images from the FLUX-1-Schnell movement of the full 7-move run
- `outputs/m4_*.mp3` — 6 Aura-2 TTS renderings of the canonical script (varied voices/tempos)
- `outputs/fast/img_*.png`, `outputs/fast/aura_*.mp3` — artifacts of the cheap `fast.py` modality pass
- `outputs/massive/img_massive_*.png` — 10 images from the 15-deep ideation run
- `outputs/index.json` — machine summary of the last full run (7 movements, 23 files, 429.9s)

The repo ships these so a stranger can inspect a real canon without spending a cent.

---

## What lives downstream

- `multi_api_v2.py` (the long-lived writers' room harness) extends this orchestra pattern with 12+ voices and 4-5 rounds of dialogue
- `mavis-flywheel` and `mavis-tap-pulse` re-use the same chord pattern but with JEV-scored gating
- `quilt-multi-oracle` is the SAME shape as move 2, but with N=4 LLM workers and a JEV composite scorer
- `quilt-spreadsheet-inference` runs the multi-LLM chord inside a 2D substrate spreadsheet (JEV + MOTH + Jepa + LLM per cell)

---

## When this doctrine applies

The orchestra is the canonical recipe for any system where:

- A claim needs to survive 12+ independent eyes before promotion
- The output is multi-modal (text + audio + image + embedding)
- Cost matters: ~$0.10/run, ~7 min wall-time
- The output becomes a substrate for downstream cells (the refined script IS a substrate walker receipt)

If you have one or more of these conditions, orchestrating N cheap models with a strong refine-pass beats one expensive model every time. This is a canon-shape.

---

## Cross-references

- **multi_api_v2.py** — the writers' room ancestor (12+ voices, 4-5 rounds)
- **quilt-multi-oracle** — multi-LLM JEV chord as substrate walker
- **mavis-tap-pulse** — chord-validated canon pulse generation
- **fleet-conductor** — orchestrates `quilt-canon-*` repos as workflows
- **quilt-canon-mcp** — canon exposed as MCP tools (probe_canon uses Llama-3.3-70B)

---

*Last expanded: 2026-09-28 — zero-shot docs pass (structure corrected against the actual tree: `scripts/` layout, no `orchestra.py`, real env vars, DeepInfra Whisper; smoke checks run and quoted). Original run data: `outputs/index.json` (run elapsed_sec=429.9, models_used={zai_chat:4, deepinfra_critics:12, cf_apis:4}, 23 output files)*
