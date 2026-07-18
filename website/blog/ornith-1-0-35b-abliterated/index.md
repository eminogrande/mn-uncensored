# Ornith 35B: can self-scaffolding survive abliteration?

Published 18 July 2026. Exact artifact: `YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated`, revision `86065d1a9008773086a177637d54ec6dc2a56cbf`.

DeepReinforce trained upstream Ornith around “self-scaffolding”: the model proposes a problem-solving scaffold, then solves inside it, with reinforcement-learning reward applied to both stages. The publisher reports 75.6 SWE-bench Verified, 50.4 SWE-bench Pro and 64.2 Terminal-Bench 2.1 for the upstream 35B checkpoint.

YuYu1015 produced a weights-only abliterated derivative. The first version reportedly damaged reasoning, so the publisher replaced the weights on 30 June 2026. For the corrected version, YuYu1015 reports hard refusals falling from roughly 99% to 5%, moralizing from roughly 95% to 14%, and GSM8K remaining at 80%. These are small publisher evaluations, not independent results. Upstream Ornith’s coding scores have not been rerun on the derivative.

The model contains 35,107,181,936 BF16 parameters, 40 layers, 256 routed experts, eight selected experts per token and a shared expert. It retains multimodal and structured-tool machinery plus thinking blocks. YuYu1015 strongly recommends repetition penalty 1.0 and warns that 1.05 can truncate output.

Primary sources:

- [Exact model card](https://huggingface.co/YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated)
- [Pinned artifact](https://huggingface.co/YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated/tree/86065d1a9008773086a177637d54ec6dc2a56cbf)
- [Official Ornith article and benchmarks](https://deep-reinforce.com/ornith_1_0.html)
- [Upstream Ornith repository](https://huggingface.co/deepreinforce-ai/Ornith-1.0-35B)
- [Official Qwen architecture card](https://huggingface.co/Qwen/Qwen3.5-35B-A3B)

The publisher’s own numbers are not zero refusal, and architecture alone does not prove post-edit vision or tool quality.
