# ABLITERATED.cloud website-v0.2.0

This release makes the catalog understandable without hiding the technical
truth.

## Real model identities

Every model card now displays the complete Hugging Face repository name:

- `huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated`
- `YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated`
- `huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated`
- `cebeuq/Ornith-1.0-397B-abliterated-W4A16`

Cards also include source-backed architecture, parameter, context, license,
multimodal, reasoning, and tool-use details while keeping the shorter `mn/*`
names clearly labeled as API shortcuts.

## Free weights, paid hosting

The model files are publicly downloadable from Hugging Face without a purchase
price. Managed inference is paid because cloud GPUs, startup, storage, network,
and operations cost money.

The site distinguishes abliterated, uncensored, decensored, and the broader
informal term jailbroken. It does not claim zero refusals, unrestricted
capability, correctness, safety, or commercial clearance.

## Planned pricing

The planned private-beta GPU-time reference rate is the current Modal GPU list
price multiplied by exactly 1.20:

- Qwen3.6 35B A3B: $5.44752/hour
- Ornith 35B: $5.44752/hour
- Qwythos 9B: $2.34144/hour
- Ornith 397B W4A16: $10.89504/hour

These are not live customer charges. Customer metering, balances, payments,
cost allocation, reconciliation, and invoicing are not implemented yet. Rates
exclude CPU, memory, storage, network, payment fees, tax, failed starts,
support, and provider price changes.

## Verification

- Complete repository test suite.
- Secret scan.
- Structured metadata and internal-resource validation.
- Exact four-model names and four planned rates asserted in tests.
- Responsive desktop and mobile visual review.
- Static website remains isolated from Modal and cannot wake a GPU.
