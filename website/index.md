---
title: ABLITERATED.cloud - Free uncensored and abliterated Hugging Face models
description: Free open-licensed Hugging Face model weights labeled uncensored, jailbroken and abliterated through a managed OpenAI-compatible cloud API.
canonical: https://eminogrande.github.io/mn-uncensored/
---

# ABLITERATED.cloud

Free model weights. Private managed access. One OpenAI-compatible API.

ABLITERATED.cloud is an open-source control plane and private evaluation service for exact pinned Hugging Face model artifacts described upstream as uncensored, decensored or abliterated. "Jailbroken" is a broader informal search term, not the exact method claimed by these model publishers.

The model files are free to download from Hugging Face. Managed cloud inference is not free: H200 and L40S GPUs, startup, storage and operations cost money. Models run with vLLM on scale-to-zero Modal GPUs. Client devices do not download model weights.

## Request access

Private-beta access is available through WhatsApp:

<https://wa.me/13103408213?text=Hi%20Emin%2C%20I%20would%20like%20to%20request%20access%20to%20ABLITERATED.cloud>

## Model catalog

### mn/god

- Artifact: `huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated`
- Revision: `8f0ee727aff5e771ea72466d64d13ecd851d2cc7`
- Hugging Face metadata: Apache-2.0, uncensored, abliterated, image-text-to-text, 36B parameters, BF16
- Context: 131,072 tokens
- Maximum output: 16,384 tokens
- Hardware: 1 x H200
- Base GPU estimate: $4.5396/hour
- Planned private-beta reference rate: $5.44752/hour
- Status: live route, currently hard-stopped

### mn/code

- Artifact: `YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated`
- Revision: `86065d1a9008773086a177637d54ec6dc2a56cbf`
- Hugging Face metadata: Apache-2.0, 35B Qwen3.5 MoE, reasoning/thinking, English and Chinese, abliterated and uncensored
- Context: 131,072 tokens
- Maximum output: 16,384 tokens
- Hardware: 1 x H200
- Base GPU estimate: $4.5396/hour
- Planned private-beta reference rate: $5.44752/hour
- Status: live route, currently hard-stopped

### mn/fast

- Artifact: `huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated`
- Revision: `efcc73cac15ff8fc5d46b8d41b53c22d571cf97d`
- Hugging Face metadata: Apache-2.0, 10B parameters, BF16, long-context, function-calling, tool-use, uncensored and abliterated
- Context: 131,072 tokens
- Maximum output: 16,384 tokens
- Hardware: 1 x L40S
- Base GPU estimate: $1.9512/hour
- Planned private-beta reference rate: $2.34144/hour
- Status: live route, currently hard-stopped

### mn/ornith-397b

- Artifact: `cebeuq/Ornith-1.0-397B-abliterated-W4A16`
- Revision: `e5651d291be1c65ff1360eee47ab533ab13b3d97`
- Legacy alias: `nuri/ornith-397b-abliterated`
- Hugging Face metadata: MIT, 397B total / about 17B active, multimodal Qwen3.5 MoE, W4A16, about 196 GB, uncensored and abliterated
- Context: 32,768 tokens configured
- Upstream context: 262,144 tokens
- Maximum output: 8,192 tokens
- Hardware: 2 x H200
- Base GPU estimate: $9.0792/hour
- Planned private-beta reference rate: $10.89504/hour
- Status: fourth route in the next budgeted release; not live in v0.3.1

The upstream terms "abliterated", "decensored" and "uncensored" describe publisher claims about reduced refusal behavior. They do not guarantee zero refusals, correctness, safety, legality or unrestricted capability. The two model cards that publish measurements still report non-zero refusal rates.

## How it works

1. An invited user receives a revocable MN Bearer token.
2. The client sends an OpenAI Chat Completions request to one gateway.
3. The gateway validates the token and resolves the exact model ID.
4. Modal starts only the selected private vLLM backend when its lifecycle is armed.
5. The GPU scales to zero after five idle minutes, or the operator hard-stops it immediately.

Five minutes is an idle tail, not a total cost limit. Startup, model loading, inference, retries, and open streams remain billable.

## API compatibility

Directly supported:

- OpenAI Chat Completions request shape
- Bearer authentication
- model listing
- streaming
- structured tool calls
- Hermes Agent
- Pi
- OpenCode
- OpenAI SDKs
- cURL and server-side applications

Cursor is a compatibility target, not a promise of complete feature parity.

## Free weights and planned managed pricing

- The exact model weight files have no purchase price on Hugging Face.
- Planned reference rate formula: current Modal GPU list price x 1.20.
- `mn/god`: $4.5396/hour base GPU; $5.44752/hour planned rate.
- `mn/code`: $4.5396/hour base GPU; $5.44752/hour planned rate.
- `mn/fast`: $1.9512/hour base GPU; $2.34144/hour planned rate.
- `mn/ornith-397b`: $9.0792/hour base GPU; $10.89504/hour planned rate.
- Current three-route planned simultaneous ceiling: $13.23648/hour.
- Future four-route planned simultaneous ceiling: $24.13152/hour.

These are not live customer charges. Customer metering, payments and invoicing are not implemented yet. Values exclude CPU, memory, storage, network, payment fees, tax and future provider price changes. A 20% markup is a 16.67% gross margin before those costs.

## Cloud and security boundary

- Model weights remain in Hugging Face and persistent Modal volumes.
- No model weights are downloaded to the operator's Mac.
- API access requires an MN Bearer token.
- Gateway-to-backend traffic uses separate private Modal proxy credentials.
- Token digests, not recoverable plaintext tokens, are stored in the shared lifecycle state.
- The public landing page never calls, polls, wakes, or embeds the inference API.

## Open source

The control plane, website, configuration, tests, deployment workflow, and documentation are public:

<https://github.com/eminogrande/mn-uncensored>

Our code uses the Apache-2.0 open-source license. Hugging Face currently displays Apache-2.0 metadata for the first three model repositories and MIT for the 397B repository. Each model still retains upstream attribution, warnings and commercial-use caveats; public weights are not automatic resale clearance.

## Current status and roadmap

Live v0.3.1 exposes three routes and all GPU containers are currently stopped. The 397B fourth route is prepared for the next release, which requires a confirmed Modal Workspace hard budget and an explicit two-H200 acknowledgement.

Roadmap:

1. Confirm the Modal Workspace hard budget.
2. Validate and release all four routes.
3. Add per-token model permissions, quotas, and rate limits.
4. Add usage metering and customer billing.
5. Complete commercial model-license and provider-term review.
6. Explore Lightning, Cashu, and Routstr payment layers.

## Machine-readable resources

- LLM index: <llms.txt>
- Full LLM context: <llms-full.txt>
- OpenAPI description: <openapi.json>
- Authentication guide: <auth.md>
- Agent skill: <skills/abliterated-cloud/SKILL.md>
- Source repository: <https://github.com/eminogrande/mn-uncensored>
