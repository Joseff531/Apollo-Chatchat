# LLM Instruction Alignment Training

A short placeholder document used by Apollo-Chatchat's sample knowledge base.

## RLHF pipeline
- **SFT**: Supervised fine-tuning on instruction/response pairs
- **Reward model**: trained on human preference comparisons
- **PPO**: Proximal Policy Optimization against the reward model
- **KL penalty**: keeps the policy close to the SFT reference

## RLHF alternatives
- **DPO** (Direct Preference Optimization) — closed-form alternative to PPO
- **IPO**, **KTO**, **ORPO** — variants that change the loss formulation
- **RLAIF** — using model-generated preferences in place of human ones

## Data construction
- High-quality demonstration sets (Dolly, OpenAssistant, ShareGPT)
- Preference pairs from human annotators or stronger models
- Constitutional-AI style critique-and-revise loops

## Evaluation
- Pairwise win-rate vs. a baseline judge model
- Reward-model score on held-out prompts
- Benchmark suites (MT-Bench, AlpacaEval, Arena Hard)

This file is intentionally a stub. Replace it with your own alignment-training docs once you have populated the sample knowledge base.
