# Ornith 397B: surgery on a model too large to hold at once

Published 18 July 2026. Exact artifact: `cebeuq/Ornith-1.0-397B-abliterated-W4A16`, revision `e5651d291be1c65ff1360eee47ab533ab13b3d97`.

Upstream Ornith contains 396,802,360,816 BF16 parameters, with roughly 17B active per token. The W4A16 derivative still occupies 210.1 GB decimal, or about 195.7 GiB, in 47 shards. Most selected language weights are symmetric four-bit integers while activations, embeddings, routers, gates, norms and the vision tower remain 16-bit.

The publisher describes a streaming pipeline that never materializes the roughly 794 GB BF16 language model. It derives refusal directions from 128 harmful and 128 harmless prompts, streams 122 source shards, projects the direction out of selected residual-writing matrices and immediately requantizes each edited tensor.

On 40 harmful prompts, the publisher reports refusal falling from 30.0% for the reference W4A16 quant to 7.5% after editing. Other reported checks include coding, structured tools, image and video smoke tests, and needle retrieval at about 127K and 252K. These are publisher tests, not independent benchmarks. Upstream Ornith’s 82.4 SWE-bench Verified score was not rerun on this derivative.

The tested deployment uses two 128 GB DGX Spark systems over 200 GbE. Our two-H200 profile remains explicitly deployment-disabled and uses a conservative 32K context.

Primary sources:

- [Exact model card](https://huggingface.co/cebeuq/Ornith-1.0-397B-abliterated-W4A16)
- [Pinned artifact](https://huggingface.co/cebeuq/Ornith-1.0-397B-abliterated-W4A16/tree/e5651d291be1c65ff1360eee47ab533ab13b3d97)
- [Pinned quantization configuration](https://huggingface.co/cebeuq/Ornith-1.0-397B-abliterated-W4A16/blob/e5651d291be1c65ff1360eee47ab533ab13b3d97/quantization_config.json)
- [Official Ornith article](https://deep-reinforce.com/ornith_1_0.html)
- [Official Qwen architecture card](https://huggingface.co/Qwen/Qwen3.5-397B-A17B)
- [Original refusal-direction paper](https://arxiv.org/abs/2406.11717)
- [Intel AutoRound](https://github.com/intel/auto-round)
