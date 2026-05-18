# LLM Inference Optimization

A short placeholder document used by Apollo-Chatchat's sample knowledge base.

## GPU memory optimization
- **PagedAttention** (vLLM) — paged KV-cache to avoid fragmentation
- **KV-cache offloading** to CPU or disk for very long contexts
- **Gradient checkpointing** is for training, not inference, but useful to know

## Compute throughput
- **Continuous batching** to keep the GPU busy across requests
- **Speculative decoding** with a smaller draft model
- **FlashAttention-2** kernels for the attention block
- **Tensor parallelism** to shard a model across multiple GPUs

## Quantization
- **INT8 / INT4** weight-only quantization (GPTQ, AWQ)
- **FP8** mixed precision on supported hardware (H100, B100)
- **GGUF** quantized formats for CPU/Metal inference (llama.cpp, Ollama)

## Serving frameworks
- **vLLM** — high-throughput serving with PagedAttention and continuous batching
- **TGI** — Hugging Face's production inference server
- **TensorRT-LLM** — NVIDIA-optimized engine
- **llama.cpp / Ollama** — efficient CPU/Apple-silicon inference

This file is intentionally a stub. Replace it with your own inference-optimization docs once you have populated the sample knowledge base.
