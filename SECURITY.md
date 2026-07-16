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

Each deployed model has an independent Modal backend and independent
scale-to-zero lifecycle. The one-container ceiling is per backend, not a global
workspace ceiling. Authenticated requests can therefore wake `mn/god`,
`mn/code`, and `mn/fast` at the same time when those routes are armed.

At the deployed catalog's documented base estimates, running all three
simultaneously is approximately `$11.0304/hour` of GPU time before other Modal
charges:

- `mn/god`: one H200, `$4.5396/hour`
- `mn/code`: one H200, `$4.5396/hour`
- `mn/fast`: one L40S, `$1.9512/hour`

The current code sets the request `routing_region`, not a constrained
`compute_region`; the routing setting does not itself add Modal's
compute-region price multiplier. A future compute-region constraint would need
its multiplier added explicitly.

The source catalog additionally retains `mn/ornith-397b`, estimated at two
H200s or `$9.0792/hour`. It has `deployment_enabled=true` for the next
budgeted release, but live `v0.3.1` still has only three routes and no running
GPU. The four-model base GPU ceiling is `$20.1096/hour`, with about `$1.6758`
of five-minute idle tails across all four. Those are next-release risk figures,
not current usage.

Scale-to-zero limits idle cost but is not a spending cap. Cold starts and the
idle shutdown window are billable. The five-minute countdown begins only after
startup, queued work, inference, streams, retries, and health activity end.

No normal CLI path may set `min_containers=1`. `mn start MODEL` must enforce
scale-to-zero, and release workflows must finish with every route hard-stopped.

Before any further GPU testing, configure a Modal Workspace hard budget. Before
sharing tokens broadly, also add per-token model permissions, quotas, rate
limits, and usage accounting. A token holder must be treated as capable of
waking every armed model that token is authorized to use.

The four-model release must refuse to begin unless the operator confirms the
Workspace hard budget and sets
`MN_RELEASE_ORNITH397=I_ACCEPT_2XH200`. It must display the two-H200 cost,
deploy and smoke-test all four routes, then hard-stop all of them. Individual
397B start, auto, wake, and launch operations require `--allow-expensive`
before lifecycle mutation.

The cost incident and corrective actions are documented in
[docs/INCIDENT-2026-07-16-MODAL-COST.md](docs/INCIDENT-2026-07-16-MODAL-COST.md).

## Model supply chain

Runtime model repositories and revisions are allowlisted in the tracked
catalog. Every revision must remain a full 40-character commit SHA. Moving
branches such as `main` are not acceptable release inputs, especially when
`trust_remote_code` is enabled.

Catalog presence and `deployment_enabled=true` do not themselves start a GPU.
The release acknowledgement and CLI expensive-model acknowledgement are
separate controls: one authorizes a validated four-route release; the other
authorizes an individual two-H200 lifecycle operation.

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
