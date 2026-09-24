# API Orchestra — Using every API, every model

A creative anthology built by orchestrating **6+ Z.AI models, 12+ DeepInfra critics, Cloudflare AI's TTS/embedding/ASR/image stack, and async Python subagents** in parallel — until the result is canon.

The point isn't to advertise how many models can be touched. The point is that **single-model generation has structural blind spots** that only become visible when N models say things differently. The orchestra finds the canon-shaped description by exhausting the disagreement.

---

## What's in here

```
api-orchestra/
├── README.md              (this file)
├── orchestra.py           (multi-LLM ZAI script → DeepInfra critics → ZAI refine)
├── orchestra2.py          (adds Cloudflare TTS + image gen)
├── orchestra3.py          (adds ASR round-trip — speak → hear → transcribe)
├── extensive.py           (ZAI + 12 DeepInfra critics)
├── fast.py                (lightweight 4-step version — sub-2-min wall-clock)
├── massive.py             (15-deep ideation across all providers in parallel)
├── ideator_brainstorm.py  (the ideator loop — 5 N-of-M waves)
├── orchestrate.py         (low-level dispatch shell, no LLM — pure provider calls)
├── outputs/               (everything produced — scripts, critiques, MP3s, PNGs)
├── *.log                  (one log per orchestration run)
└── index.json             (machine-readable summary of the last run)
```

---

## The recipe — 7 movements

| Move | Inputs | Outputs | Models |
|------|--------|---------|--------|
| **1 — script draft** | topic + canon-context | 12-slot "movie script" | ZAI GLM-5.3-Flash, GLM-5.1, GLM-5.2, GLM-4.6 |
| **2 — critique chord** | the script | 12 critic reviews | DeepInfra Qwen3 / Llama-3.3 / DeepSeek-V3 / Kimi-K3 / Mistral / Ling / Nemotron / Llama-4 / Gemma-4 / Claude-Opus / ByteDance Seed-2.0 |
| **3 — refine pass** | script + critiques | canonical script | ZAI GLM-5.3-Flash (best-of-best wins as the canonical script) |
| **4 — voice** | canonical script | 6 MP3s | Cloudflare Aura-2 TTS (varied voices, varied tempos) |
| **5 — image** | canonical script + topics | 5 PNGs | Cloudflare FLUX-1-Schnell |
| **6 — embeddings** | canonical script | 7 vectors | Cloudflare BGE-M3 (768-dim) |
| **7 — ASR round-trip** | MP3s | transcribed JSON | Cloudflare Whisper |

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
cd /workspace/repos/api-orchestra

# Cheap version (~2 min, 4 moves)
python3 fast.py --topic "the substrates speak"

# Standard version (~7 min, 7 moves, full pipeline)
python3 orchestra.py --topic "the substrates speak"

# Maximum version (~10 min, 12 critics)
python3 extensive.py --topic "the substrates speak"

# Ideator brainstorms (~3 min, 5 waves × N ideas)
python3 ideator_brainstorm.py
```

Each run writes outputs to `outputs/<run-stamp>/` and updates `index.json` with the summary.

**Required env**: `ZAI_TOKEN`, `DEEPINFRA_TOKEN`, `CLOUDFLARE_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`.
**Optional env**: `GEMINI_TOKEN` (alt critic), `GROQ_TOKEN` (alt model).

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

*Last expanded: 2026-09-24 — pulled from `outputs/index.json` (run elapsed_sec=429.9, models_used={zai_chat:4, deepinfra_critics:12, cf_apis:4}, 23 output files)*
