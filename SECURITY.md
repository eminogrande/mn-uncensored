# Security

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

## Public service warning

This first release is a private evaluation deployment, not a complete
multi-tenant resale platform. Before public access, add metering, quotas, rate
limits, abuse handling, billing reconciliation, audit logging without prompt
content, terms, privacy controls, and model/license review.
