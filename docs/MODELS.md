# Model catalog, licenses, and deployment status

This document records the exact model artifacts configured for MN Uncensored.
It is an operational attribution and release record, not legal advice.

All three public MN model IDs currently use a 131,072-token deployed context
window and a 16,384-token configured output ceiling. Those are deployment
limits, not claims about the maximum capability of the upstream checkpoints.
Only behavior measured against the exact pinned artifact and current runtime
may be reported as an MN benchmark.

## Runtime catalog

| MN model | Runtime Hugging Face artifact | Pinned revision | Metadata license | Hardware estimate |
| --- | --- | --- | --- | --- |
| `mn/god` | [`huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated`](https://huggingface.co/huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated) | `8f0ee727aff5e771ea72466d64d13ecd851d2cc7` | Apache-2.0 | 1 x H200, about $4.54/hour |
| `mn/code` | [`YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated`](https://huggingface.co/YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated) | `86065d1a9008773086a177637d54ec6dc2a56cbf` | Apache-2.0 | 1 x H200, about $4.54/hour |
| `mn/fast` | [`huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated`](https://huggingface.co/huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated) | `efcc73cac15ff8fc5d46b8d41b53c22d571cf97d` | Apache-2.0 | 1 x L40S, about $1.95/hour |

The hourly amounts are catalog estimates based on base Modal GPU prices. They
exclude CPU gateway usage, storage, network charges, taxes, and any regional
price multiplier. Each backend has its own one-container ceiling, so all three
can be billable simultaneously. The approximate combined base GPU cost is
`$11.03/hour`.

## `mn/god`: documented compatibility fallback

The originally selected checkpoint is:

- [`WWTCyberLab/qwen3.6-35B-A3B-abliterated`](https://huggingface.co/WWTCyberLab/qwen3.6-35B-A3B-abliterated)
- revision `ee52b4424de95203ed585725f10912d059c60aa7`
- Apache-2.0 license metadata
- base model [`Qwen/Qwen3.6-35B-A3B`](https://huggingface.co/Qwen/Qwen3.6-35B-A3B)

That pin declares the architecture `Qwen3_5MoeForCausalLM`, which is not
registered by the selected vLLM 0.21 runtime. MN therefore currently deploys
the Huihui checkpoint listed in the runtime table. Its pin declares the
compatible `Qwen3_5MoeForConditionalGeneration` architecture.

This is a technical fallback, not an equivalence claim:

- `mn/god` must be identified as the Huihui runtime artifact in deployment and
  release records.
- Results, behavior, safety characteristics, or benchmarks from the WWT
  checkpoint must not be attributed to the Huihui checkpoint.
- Changing back to WWT requires a runtime compatibility test and a catalog
  revision; it must not happen through an unpinned model override.

Both derivative repositories declare Apache-2.0 in their Hugging Face metadata
and identify Qwen 3.6 35B A3B as the base. Neither derivative pin includes its
own `LICENSE` or `NOTICE` file. The Huihui card links to the
[Qwen Apache-2.0 license](https://huggingface.co/Qwen/Qwen3.6-35B-A3B/blob/main/LICENSE).
The WWT card describes research and educational intent. The Huihui card
recommends research, testing, or controlled environments and cautions against
direct public-facing commercial deployment. These statements must remain
visible in any commercial-clearance review even though the repository metadata
labels the weights Apache-2.0.

## `mn/code`: Ornith attribution chain

The runtime artifact is the exact YuYu pin shown in the catalog. Its Hugging
Face metadata declares Apache-2.0 and identifies
[`deepreinforce-ai/Ornith-1.0-35B`](https://huggingface.co/deepreinforce-ai/Ornith-1.0-35B)
as its base model.

The Ornith base metadata declares MIT and describes the model as post-trained
on Qwen 3.5. The exact Qwen base checkpoint is not declared in the Ornith Hub
metadata. The YuYu derivative and reviewed Ornith repository listing do not
include a license file at the reviewed revisions, so release records must
retain:

- the YuYu artifact ID, full pin, and Apache-2.0 metadata declaration;
- the DeepReinforce Ornith attribution and MIT metadata declaration;
- the upstream model-card links and any notices supplied with redistributed
  artifacts.

Benchmarks reported by DeepReinforce for the aligned Ornith base are not
benchmarks of the YuYu abliterated derivative or of the deployed MN service.

## `mn/fast`: Qwythos attribution and context caveat

The runtime artifact is the exact Huihui Qwythos pin shown in the catalog. Its
metadata declares Apache-2.0 and identifies
[`empero-ai/Qwythos-9B-Claude-Mythos-5-1M`](https://huggingface.co/empero-ai/Qwythos-9B-Claude-Mythos-5-1M)
as its base. That base also declares Apache-2.0 and identifies
[`Qwen/Qwen3.5-9B`](https://huggingface.co/Qwen/Qwen3.5-9B) as its base model.

The derivative and Qwythos base repository listings reviewed for this release
do not include their own `LICENSE` or `NOTICE` file. Preserve the full
attribution chain and the upstream Qwen license when redistributing artifacts.

The Qwythos card reports training that includes Claude Mythos and Claude Fable
traces. Apache-2.0 weight metadata does not by itself establish rights to every
training-data source or clear the model for resale. Obtain legal and
contractual review before public commercial use.

The `1M` name is not the current MN deployment limit. The catalog serves
131,072 tokens. Do not advertise a one-million-token MN context until the exact
pinned artifact, vLLM configuration, hardware, latency, and memory behavior
have been tested at that size.

The Huihui card recommends research, testing, or controlled environments and
cautions against direct public-facing commercial deployment. Keep that warning
with any product-readiness assessment.

## Release rules

Before changing or releasing this catalog:

1. Resolve every runtime artifact to a full 40-character Hugging Face commit
   SHA.
2. Record the model and base-model license metadata and check each repository
   for actual `LICENSE` and `NOTICE` files.
3. Document any runtime substitution, mirror, quantization, or conversion as a
   separate artifact; never silently present it as the requested checkpoint.
4. Run compatibility and behavior tests against the exact pinned artifact.
5. Keep benchmark claims tied to the exact artifact, runtime, prompt harness,
   and test date.
6. Recalculate the simultaneous GPU ceiling and verify workspace spending
   controls.
7. Complete legal and infrastructure-terms review before paid or public
   access.
