# Security

## Scope and trust boundary

The GitHub repository may be public. The deployed API is still a private
evaluation service and must remain authenticated.

The public model catalog, MN model IDs, Modal application names, gateway URL,
backend URLs, hardware profiles, and pinned Hugging Face revisions are not
secrets. Publishing them does not grant backend access. The vLLM backends
remain protected by Modal proxy authentication, and the gateway requires an MN
Bearer token for model and status routes.

Do not treat an unshared URL as access control. A valid token is required even
for private testing.

## Credential storage

MN uses three credential layers:

1. The private vLLM backend accepts only Modal proxy credentials.
2. The CPU gateway holds those proxy credentials in the Modal Secret
   `nuri-backend-proxy`.
3. Users authenticate to the gateway with `Authorization: Bearer sk-mn-...`.

The gateway stores SHA-256 token digests in the Modal Dict `nuri-api-state`.
Plaintext API tokens cannot be recovered from that Dict.

The local owner token is stored in the macOS login Keychain as
`mn-uncensored-owner-token`. The Modal proxy credentials are stored locally as
`uncensored-modal-key` and `uncensored-modal-secret`.

Never commit or publish:

- Modal proxy keys or secrets
- Hugging Face access tokens
- plaintext MN API tokens
- `.env`, `.env.*`, or `deployment.env`
- local Pi authentication, settings, or session files
- local `.mn/` runtime state

The tracked model catalog must contain public, non-secret deployment metadata
only. Backend destinations are selected from that fixed catalog; clients must
not be allowed to supply arbitrary backend URLs.

## Before every commit

Review staged filenames and scan staged content:

```sh
git diff --cached --name-only
git diff --cached --check
./scripts/check-secrets.sh
```

Never bypass the SSH signing configuration. Commits and tags must remain signed.

## Token response

If a friend token may be exposed:

```sh
mn token revoke <name>
mn token create <replacement-name>
```

If a Modal proxy credential may be exposed, rotate the workspace proxy token,
replace both macOS Keychain entries, and overwrite the Modal
`nuri-backend-proxy` secret before starting the model again.

If a Hugging Face token may be exposed, revoke it at Hugging Face, replace the
corresponding local or Modal secret, and verify that it was not retained in Git
history or a release artifact.

## Cost and availability boundary

Each catalog model has an independent Modal backend and independent
scale-to-zero lifecycle. The one-container ceiling is per backend, not a global
workspace ceiling. Authenticated requests can therefore wake `mn/god`,
`mn/code`, and `mn/fast` at the same time.

At the catalog's documented base estimates, running all three simultaneously
is approximately `$11.03/hour` of GPU time before any regional multiplier or
other Modal charges:

- `mn/god`: one H200, approximately `$4.54/hour`
- `mn/code`: one H200, approximately `$4.54/hour`
- `mn/fast`: one L40S, approximately `$1.95/hour`

Scale-to-zero limits idle cost but is not a spending cap. Cold starts and the
idle shutdown window are billable. Before sharing tokens broadly, configure a
Modal workspace budget and add per-token model permissions, quotas, rate
limits, and usage accounting. A token holder must be treated as capable of
waking every model that token is authorized to use.

## Model supply chain

Runtime model repositories and revisions are allowlisted in the tracked
catalog. Every revision must remain a full 40-character commit SHA. Moving
branches such as `main` are not acceptable release inputs, especially when
`trust_remote_code` is enabled.

The model cards, license metadata, attribution chain, deployment exceptions,
and commercial-use caveats are documented in
[docs/MODELS.md](docs/MODELS.md). Model metadata is not a substitute for legal
review. Do not market an abliterated checkpoint as having the benchmark results
of its base model or of another checkpoint.

## Public service warning

The source repository is public, but the deployed API is a private evaluation
service, not a complete multi-tenant resale platform. Before public access, add
metering, quotas, rate limits, abuse handling, billing reconciliation, audit
logging without prompt content, terms, privacy controls, incident response,
and model/license review.

The current tokens are access credentials, not customer billing accounts. Do
not expose this service as a paid public API until authorization, usage
isolation, spending controls, and legal clearance have been implemented and
tested.
