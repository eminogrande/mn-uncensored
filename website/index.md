---
title: ABLITERATED.cloud - Open models. One private API.
description: Exact pinned Hugging Face models through a token-protected OpenAI-compatible API powered by vLLM and scale-to-zero cloud GPUs.
canonical: https://eminogrande.github.io/mn-uncensored/
---

# ABLITERATED.cloud

Open models. Private access. One OpenAI-compatible API.

ABLITERATED.cloud is an open-source control plane and private evaluation service for exact pinned Hugging Face model artifacts. Models run with vLLM on scale-to-zero Modal GPUs. Client devices do not download model weights.

## Request access

Private-beta access is available through WhatsApp:

<https://wa.me/13103408213?text=Hi%20Emin%2C%20I%20would%20like%20to%20request%20access%20to%20ABLITERATED.cloud>

## Model catalog

### mn/god

- Artifact: `huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated`
- Revision: `8f0ee727aff5e771ea72466d64d13ecd851d2cc7`
- Context: 131,072 tokens
- Maximum output: 16,384 tokens
- Hardware: 1 x H200
- Base GPU estimate: $4.5396/hour
- Status: live route, currently hard-stopped

### mn/code

- Artifact: `YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated`
- Revision: `86065d1a9008773086a177637d54ec6dc2a56cbf`
- Context: 131,072 tokens
- Maximum output: 16,384 tokens
- Hardware: 1 x H200
- Base GPU estimate: $4.5396/hour
- Status: live route, currently hard-stopped

### mn/fast

- Artifact: `huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated`
- Revision: `efcc73cac15ff8fc5d46b8d41b53c22d571cf97d`
- Context: 131,072 tokens
- Maximum output: 16,384 tokens
- Hardware: 1 x L40S
- Base GPU estimate: $1.9512/hour
- Status: live route, currently hard-stopped

### mn/ornith-397b

- Artifact: `cebeuq/Ornith-1.0-397B-abliterated-W4A16`
- Revision: `e5651d291be1c65ff1360eee47ab533ab13b3d97`
- Legacy alias: `nuri/ornith-397b-abliterated`
- Context: 32,768 tokens configured
- Maximum output: 8,192 tokens
- Hardware: 2 x H200
- Base GPU estimate: $9.0792/hour
- Status: fourth route in the next budgeted release; not live in v0.3.1

The upstream term "abliterated" describes a checkpoint. It is not a guarantee of zero refusals, correctness, safety, or unrestricted capability.

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

## Cost transparency

- Current three-route simultaneous ceiling: $11.0304/hour in base GPU charges.
- Future four-route simultaneous ceiling: $20.1096/hour in base GPU charges.
- Current three five-minute idle tails: $0.9192.
- Future four five-minute idle tails: $1.6758.

These values exclude CPU, memory, storage, network, tax, and future provider price changes.

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

Our code uses the Apache-2.0 open-source license. Each model retains its own upstream license and commercial-use caveats.

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
