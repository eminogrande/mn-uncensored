# Inside Huihui-Qwen3.6: 256 experts, 3B active parameters, and one refusal direction

Published 18 July 2026. Exact artifact: `huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated`, revision `8f0ee727aff5e771ea72466d64d13ecd851d2cc7`.

Qwen3.6 35B A3B is a sparse multimodal mixture-of-experts model with 35,951,822,704 stored BF16 parameters and about 3B active for each token. Its 40 language layers combine 256-expert MoE blocks, Gated DeltaNet and periodic full attention. Native context is 262,144 tokens; the repository is roughly 71.9 GB.

Qwen released the upstream checkpoint on 15 April 2026. Huihui published this abliterated derivative three days later, describing it as an uncensored proof of concept. Abliteration compares activations produced by harmful and harmless prompts, estimates a direction associated with refusal, and projects that direction out of selected weights. It is a weight edit, not a prompt jailbreak or conventional fine-tune.

The upstream Qwen model reports 73.4 SWE-bench Verified, 67.2 SWE-bench Multilingual, 49.5 SWE-bench Pro, 51.5 Terminal-Bench 2.0 and 37.0 MCPMark. Those results do **not** belong to the abliterated derivative: Huihui publishes no post-edit benchmark or refusal-rate evaluation for this checkpoint.

Primary sources:

- [Exact model card](https://huggingface.co/huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated)
- [Pinned artifact](https://huggingface.co/huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated/tree/8f0ee727aff5e771ea72466d64d13ecd851d2cc7)
- [Official upstream Qwen card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B)
- [Official Qwen release article](https://qwen.ai/blog?id=qwen3.6-35b-a3b)
- [Original refusal-direction paper](https://arxiv.org/abs/2406.11717)
- [Implementation linked by huihui-ai](https://github.com/Sumandora/remove-refusals-with-transformers)

The publisher warns that safety filtering is reduced and recommends controlled research use. “Abliterated” means refusal-reduced, not zero-refusal, correct, legal or harmless.
