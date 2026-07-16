# ABLITERATED.cloud authentication

ABLITERATED.cloud uses revocable MN Bearer tokens for the OpenAI-compatible API.

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

## OAuth status

OAuth is not currently implemented. Do not attempt OAuth discovery or represent MN Bearer tokens as OAuth access tokens.

## Request access

Contact:
https://wa.me/13103408213?text=Hi%20Emin%2C%20I%20would%20like%20to%20request%20access%20to%20ABLITERATED.cloud
