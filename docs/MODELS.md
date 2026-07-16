# Model catalog, licenses, and deployment status

This document records the exact model artifacts configured for MN Uncensored.
It is an operational attribution and release record, not legal advice.

The source catalog contains four pinned MN model records. Three are deployed
through the current gateway and use a 131,072-token context window with a
16,384-token output ceiling. The fourth, `mn/ornith-397b`, is prepared with a
conservative 32,768-token context and 8,192-token output ceiling for the next
budgeted release. Live `v0.3.1` still has only the first three routes and no
running GPU.

Those are MN endpoint settings, not claims about the maximum capability of the
upstream checkpoints. Only behavior measured against the exact pinned artifact
and current runtime may be reported as an MN benchmark.

## Source catalog and deployment status

| MN model | Exact Hugging Face artifact | Pinned revision | Metadata license | MN endpoint limits | Hardware estimate | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `mn/god` | [`huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated`](https://huggingface.co/huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated) | `8f0ee727aff5e771ea72466d64d13ecd851d2cc7` | Apache-2.0 | 131,072 context / 16,384 output | 1 x H200, $4.5396/hour | Deployed route, currently hard-stopped |
| `mn/code` | [`YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated`](https://huggingface.co/YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated) | `86065d1a9008773086a177637d54ec6dc2a56cbf` | Apache-2.0 | 131,072 context / 16,384 output | 1 x H200, $4.5396/hour | Deployed route, currently hard-stopped |
| `mn/fast` | [`huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated`](https://huggingface.co/huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated) | `efcc73cac15ff8fc5d46b8d41b53c22d571cf97d` | Apache-2.0 | 131,072 context / 16,384 output | 1 x L40S, $1.9512/hour | Deployed route, currently hard-stopped |
| `mn/ornith-397b` | [`cebeuq/Ornith-1.0-397B-abliterated-W4A16`](https://huggingface.co/cebeuq/Ornith-1.0-397B-abliterated-W4A16) | `e5651d291be1c65ff1360eee47ab533ab13b3d97` | MIT | 32,768 context / 8,192 output | 2 x H200, $9.0792/hour | `deployment_enabled=true`; fourth route in next budgeted release, not live in v0.3.1 |

The hourly amounts are catalog estimates based on base Modal GPU prices. They
exclude CPU gateway usage, storage, network charges, and taxes. The current
`routing_region` setting routes requests and does not itself add a
compute-region multiplier; such a multiplier would need to be included if
`compute_region` were constrained later. The three live routes have a combined
base GPU ceiling of `$11.0304/hour`. The next budgeted release adds
`mn/ornith-397b`; the four-model ceiling is `$20.1096/hour`, and five idle
minutes across all four cost about `$1.6758` before other charges.

The four-model figure is the next-release risk ceiling, not current usage:
live `v0.3.1` has only three hard-stopped routes.

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

## `mn/ornith-397b`: retained large-model record

The retained large-model artifact is:

- [`cebeuq/Ornith-1.0-397B-abliterated-W4A16`](https://huggingface.co/cebeuq/Ornith-1.0-397B-abliterated-W4A16)
- revision `e5651d291be1c65ff1360eee47ab533ab13b3d97`
- public MN ID `mn/ornith-397b`
- reserved legacy alias `nuri/ornith-397b-abliterated`
- MIT license metadata
- base model
  [`deepreinforce-ai/Ornith-1.0-397B`](https://huggingface.co/deepreinforce-ai/Ornith-1.0-397B)

The model card describes a 397B-parameter, approximately 17B-active
Qwen3.5-MoE multimodal model, a roughly 196 GB W4A16 artifact, native
262,144-token context, and vLLM 0.17 or newer. Its published DGX Spark example
used `qwen3_coder` and reports tests at 128K and 256K. Those upstream choices
and claims are not validation of an MN Modal deployment.

The retained MN profile deliberately records only 32,768 context and 8,192
maximum output. Those conservative values reflect the historically exercised
endpoint configuration, not the model card's native ceiling. Increasing them
requires a new budgeted compatibility, memory, latency, streaming, and
tool-calling validation on the exact target hardware.

The reintroduced source profile records `qwen3_xml` tool parsing because the
pinned chat template uses function/parameter XML, `qwen3` reasoning with
thinking disabled by default, `language_model_only=false` to retain the
multimodal artifact, and prefix caching disabled. The old prototype used
`qwen3_coder` and experimental Mamba-aligned prefix caching; those choices are
historical and must not be restored without exact-runtime tests. Pi may
advertise reasoning support, but clients must still handle the model's
reasoning output correctly.

This model is prepared with `deployment_enabled=true` for the next budgeted
release. That release deploys a static scale-to-zero backend and adds it to the
gateway and agent catalogs, but leaves it hard-stopped. CLI start, auto, wake,
and launch operations require explicit `--allow-expensive` acknowledgement
before state mutation. Its estimated two-H200 rate is `$9.0792/hour`,
`$0.15132/minute`, or `$0.7566` for a five-minute idle tail.

The release workflow refuses to begin unless
`MN_RELEASE_ORNITH397=I_ACCEPT_2XH200` is set. With that acknowledgement and a
confirmed Workspace hard budget, it deploys all four backends and runs ordinary
text, streaming, forced structured tool calling, at least one text-plus-image
397B smoke test, scale-to-zero observation, and hard-stop verification.

The earlier `nuri-ornith-397b` prototype used the same pinned artifact, but
that historical app is stopped. Keeping a source record does not reactivate or
redeploy that app.

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
4. Require an explicit expensive-model acknowledgement for multi-GPU lifecycle
   operations and verify it fails before state mutation when omitted.
5. Run compatibility and behavior tests against the exact pinned artifact.
6. Keep benchmark claims tied to the exact artifact, runtime, prompt harness,
   and test date.
7. Recalculate the simultaneous GPU ceiling and verify workspace spending
   controls.
8. Complete legal and infrastructure-terms review before paid or public
   access.
