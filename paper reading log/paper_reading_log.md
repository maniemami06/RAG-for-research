# Reading Log — LLM Quantization & Low-Bit Inference

> One entry per paper. Fill this in as you read each paper for your gold Q&A set — it should take 20-30 min per paper if you've already understood it well enough to write eval questions. Copy the template block below for each new paper.

---

## Index

| # | Paper | Year | Granularity | Recovery Method | Status |
|---|-------|------|-------------|------------------|--------|
| 1 | ZeroQuant | 2022 | group-wise (W) + token-wise (A) | Layer-by-layer KD | ✅ done |
| 2 | | | | | |

*(Keep this table updated — it becomes your at-a-glance corpus map, and the two axis columns are exactly what you'll use to compare papers against each other.)*

---

## Template (copy for each paper)

### [Paper Title] — [Authors, Year, arXiv ID]

**One-sentence summary**
What does this paper do, in one sentence, as if explaining to another researcher who hasn't read it?

**Problem it addresses**
What specific gap or failure in prior work motivated this paper? (1-3 sentences)

**Method — the core idea**
The actual mechanism, in your own words. Not the abstract's wording — explain it like you're teaching someone.

**Where it sits on the two axes**
- Granularity: (per-tensor / per-group / per-channel / per-token / other)
- Recovery method: (none / calibration only / distillation / QAT / other)

**Key numbers**
The 2-4 results that matter most (accuracy retained, speedup, memory reduction, model sizes tested). Numbers, not vibes — these are what your gold answers will need to cite precisely.

**How it relates to other papers in the corpus**
What does it build on? What does it get compared against or superseded by? (Fill this in retroactively as you read more — early entries will be sparse here, that's fine.)

**One limitation or open question**
Something the paper doesn't fully solve, an assumption it makes, or a question you were left with. This is the "critical reading" signal — don't skip it even if it feels awkward to critique a paper you don't fully understand yet.

**Gold Q&A seeds**
2-3 rough question ideas this paper suggests for your eval set (you'll refine these later, this is just capture-while-fresh).

---

## Example (filled in)

### ZeroQuant — Yao et al., 2022, arXiv:2206.01861

**One-sentence summary**
ZeroQuant makes post-training INT8 quantization of large transformers accurate and fast by using finer-grained scale factors (per weight-group, per activation-token) instead of one scale factor per tensor, plus a cheap layer-by-layer distillation step instead of full retraining.

**Problem it addresses**
Simple PTQ (one scale factor per tensor) degrades badly on large transformers because weight/activation value ranges vary a lot across the tensor, and outliers force a bad trade-off between precision and range. Full QAT fixes this but needs the entire training pipeline and dataset, which is often infeasible at GPT-3 scale.

**Method — the core idea**
Split weight matrices into groups, each with its own scale factor (group-wise quantization). Compute activation scale factors per token, dynamically, at inference time (token-wise quantization). For the accuracy that's still lost, distill knowledge layer-by-layer from the FP16 teacher into the quantized student, rather than fine-tuning the whole model end-to-end — this needs only calibration data, not the original training set. Custom CUDA kernels were written to actually realize speedups from these finer-grained schemes.

**Where it sits on the two axes**
- Granularity: group-wise (weights) + token-wise (activations)
- Recovery method: layer-by-layer knowledge distillation (LKD)

**Key numbers**
Tested up to GPT-3-350M and GPT-J scale; reported ~2-5x latency reduction and ~3x memory footprint reduction with minimal accuracy loss vs FP16 baseline. (Go back and pull exact figures from the results tables before finalizing gold answers.)

**How it relates to other papers in the corpus**
Precursor to ZeroQuant-V2. Often cited alongside SmoothQuant, GPTQ, and AWQ as part of the same "how do you handle activation outliers cheaply" problem — each proposes a different fix (SmoothQuant: shift the outlier burden from activations to weights; GPTQ: weight-only, optimal per-layer rounding via Hessian info; AWQ: protect a small % of "salient" weight channels instead of quantizing everything uniformly).

**One limitation or open question**
LKD still requires calibration data and a per-layer training loop — cheaper than full QAT, but not free. Also unclear from this paper alone how well the method scales past the sizes they tested (175B is mentioned but less thoroughly benchmarked than smaller scales).

**Gold Q&A seeds**
- Why does token-wise (not per-tensor) activation quantization matter for transformers specifically?
- What's the difference between LKD and standard end-to-end knowledge distillation, and why does that difference matter for cost?
- What failure mode does group-wise quantization specifically fix that per-tensor quantization can't?