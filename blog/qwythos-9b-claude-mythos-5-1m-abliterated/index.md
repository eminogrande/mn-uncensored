# Qwythos has three lives: Qwen bones, 500M reasoning tokens and an abliterated refusal circuit

Published 18 July 2026. Exact artifact: `huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated`, revision `efcc73cac15ff8fc5d46b8d41b53c22d571cf97d`.

Qwythos begins as dense Qwen3.5-9B architecture, then receives a full-parameter reasoning fine-tune from Empero, then goes through huihui-ai’s refusal-reduction process. The exact child has 9,653,104,368 BF16 parameters and occupies roughly 19.3 GB.

Empero says it trained the text backbone on more than 500 million tokens of Claude Mythos, Claude Fable and in-house reasoning traces. Its 100-example matched evaluation reports large MMLU and GSM8K gains, a small ARC gain, and a GPQA Diamond regression. The vision tower was frozen and not evaluated.

The model is configured for 1,048,576 tokens through static YaRN, but Empero reports smoke testing at roughly 137K. Our hosted profile therefore uses 131,072. The million-token label is configuration, not proof of million-token reasoning quality.

Huihui publishes no post-abliteration refusal test or benchmark rerun. Empero’s numbers belong to the pre-edit checkpoint.

Primary sources:

- [Exact Huihui model card](https://huggingface.co/huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated)
- [Pinned artifact](https://huggingface.co/huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated/tree/efcc73cac15ff8fc5d46b8d41b53c22d571cf97d)
- [Empero Qwythos card, training and evaluations](https://huggingface.co/empero-ai/Qwythos-9B-Claude-Mythos-5-1M)
- [Official Empero site](https://empero.org/)
- [Official Qwen3.5-9B repository](https://huggingface.co/Qwen/Qwen3.5-9B)
- [Original refusal-direction paper](https://arxiv.org/abs/2406.11717)
