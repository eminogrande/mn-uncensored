# ABLITERATED.cloud authentication

ABLITERATED.cloud uses revocable Bearer access tokens for the OpenAI-compatible inference API.

## Request header

```http
Authorization: Bearer sk-mn-...
```

The public website never contains or retrieves a token.

## Token behavior

- A missing token returns an OpenAI-style `401` error.
- An invalid or revoked token returns an OpenAI-style `401` error.
- Tokens are created and revoked by the operator.
- The shared gateway stores token digests, not recoverable plaintext tokens.
- User tokens are separate from Modal account credentials.
- Gateway-to-backend proxy credentials are separate from user tokens.

## Lifecycle requirement

A valid token cannot wake a hard-stopped route. The operator must explicitly arm or start one model first.

The 397B route additionally requires explicit operator cost acknowledgement for start, automatic mode, wake, or agent launch.

## OAuth and agent-discovery status

The public website exposes OAuth-style discovery and anonymous read-only registration for agents that inspect public model metadata. That public credential does not authorize inference. The model API itself currently uses operator-issued Bearer tokens; inference OAuth is not implemented.

## Request access

Contact through Signal and mention ABLITERATED.cloud:
https://signal.me/#p/+13103408213
