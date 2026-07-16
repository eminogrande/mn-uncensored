# Modal GPU cost incident — 2026-07-16

## Summary

MN Uncensored incurred `$45.9634` of Modal resource usage on 2026-07-16 before
credits. The incident was caused by unsafe lifecycle semantics and heavy
development/cold-start churn, not by a demonstrated failure of Modal's stable
idle scale-down.

The most serious product error was naming a persistent warm mode `mn start`.
That command set `min_containers=1`. Modal cannot scale below the configured
minimum, so its five-minute `scaledown_window` could never reduce that route to
zero. A user reasonably expected “start” to be protected by automatic
shutdown; the implementation did not meet that expectation.

## User impact

Modal's billing report returned the following raw usage before credits:

| Application | Cost |
| --- | ---: |
| Legacy `nuri-ornith-397b` | $32.8227 |
| `mn/god` | $9.4604 |
| `mn/code` | $3.1430 |
| `mn/fast` | $0.5121 |
| `mn-uncensored-api` | $0.0252 |
| **Total** | **$45.9634** |

Resource totals:

| Resource | Cost |
| --- | ---: |
| H200 | $42.9209 |
| L40S | $0.4897 |
| CPU | $1.7400 |
| Memory | $0.8128 |

These reports are before Modal credits and can lag by several minutes. The
Modal Usage & Billing page and eventual invoice are authoritative for the
amount charged.

## Verified timeline

Hourly raw costs in Europe/Berlin:

| Hour | Cost | Dominant application |
| --- | ---: | --- |
| 08:00 | $3.2887 | Legacy 397B |
| 09:00 | $6.0872 | Legacy 397B |
| 10:00 | $7.0479 | Legacy 397B |
| 11:00 | $6.3032 | Legacy 397B |
| 12:00 | $7.2341 | Legacy 397B |
| 13:00 | $2.8736 | Legacy 397B |
| 16:00 | $4.1379 | `mn/god` |
| 17:00 | $6.2956 | Catalog development |
| 18:00 | $2.6951 | Catalog development |
| 19:00 | $0.0001 | Gateway only |

Modal app and container history showed:

- 26 legacy 397B GPU starts across three app IDs;
- 23 `mn/god` server starts during repeated deployments and debugging;
- the final stable legacy auto session served inference around 13:09 and shut
  down around 13:19, approximately ten minutes after the request;
- the last observed `mn/god` container became ready around 18:10 and stopped
  around 18:19;
- after containment, Modal reported zero running containers and zero tasks for
  every model app.

## Technical causes

### 1. Ordinary `start` meant permanent warm capacity

The old CLI executed:

```python
server.update_autoscaler(
    min_containers=1,
    max_containers=1,
    scaledown_window=300,
)
```

`min_containers=1` is a floor. The idle window controls how long an excess or
zero-minimum container may remain idle; it cannot override the minimum and
scale a one-container floor to zero.

This was a design and naming failure in MN.

### 2. Cold-start polling created redundant starts

Before `v0.3.1`, the gateway polled cold Modal Servers every five seconds.
Each empty Modal 503 could trigger or join scale-up work. Long downloads,
compilation, failed starts, and rapid redeployments accumulated many pending
GPU invocations.

`v0.3.1` replaced that polling with exponential backoff.

### 3. Development repeatedly restarted expensive backends

The same day included many code fixes and Modal deployments. A deploy, health
probe, smoke test, retry, or inference request is activity and can start or
keep a GPU running. The catalog was not sitting idle for all of the charged
period; it was being repeatedly started and replaced.

### 4. The legacy 397B app was a separate deployment

The old `nuri-ornith-397b` service existed separately from the later
`mn/god`, `mn/code`, and `mn/fast` catalog. New catalog lifecycle commands did
not retroactively control every historical app ID.

The exact artifact was
[`cebeuq/Ornith-1.0-397B-abliterated-W4A16`](https://huggingface.co/cebeuq/Ornith-1.0-397B-abliterated-W4A16)
at revision `e5651d291be1c65ff1360eee47ab533ab13b3d97`, using two H200s at an
estimated base rate of `$9.0792/hour`. Its high rate made repeated starts and
unsafe warm capacity especially costly.

## Why five-minute auto-stop is not a spending cap

The idle timer begins only after there is no active or queued backend work.
These periods remain billable:

- GPU allocation and container startup;
- downloading or restoring weights;
- loading weights into GPU memory;
- CUDA/kernel compilation;
- health checks and queued retries;
- inference and open streams;
- the final five-minute idle tail.

A stuck 30-minute startup can therefore cost 30 minutes plus any final idle
period. A five-minute idle window limits idle tail cost; it is not a
five-minute maximum session runtime.

The real outer protection is the Modal Workspace hard budget:
<https://modal.com/docs/guide/budgets>.

## Immediate containment

Executed on 2026-07-16:

```sh
mn stop
```

Verified:

- `mn/god`: stopped;
- `mn/code`: stopped;
- `mn/fast`: stopped;
- legacy `nuri-ornith-397b`: stopped;
- all model apps: zero tasks;
- Modal container list: empty.

## Permanent corrective actions

The following changes are implemented in the repository. They are not to be
deployed or exercised against a GPU until the Modal Workspace hard budget is
confirmed:

- `mn start MODEL` now enforces scale-to-zero, arms one explicit model, and
  wakes it once.
- No normal CLI command can set `min_containers=1`.
- `mn start`, `mn auto`, and `mn wake` require an explicit model.
- Default idle shutdown changed from ten to five minutes.
- Configuration validation rejects idle shutdown values above 300 seconds.
- Backend startup timeout reduced from 90 to 30 minutes.
- Automatic mode reapplies `min_containers=0`, `max_containers=1`, and the
  tracked idle window even if a previous dynamic override existed.
- Release smoke tests end with all models hard-stopped.
- Tests assert that the scale-to-zero policy cannot keep a warm container.
- More GPU testing is blocked operationally until a Workspace budget is set.
- The exact 397B artifact is retained as the source-catalog record
  `mn/ornith-397b`, with legacy alias `nuri/ornith-397b-abliterated`, so its
  cost and supply-chain metadata remain visible.
- That retained record has `deployment_enabled=true` for the next budgeted
  release. Live `v0.3.1` remains unchanged with three routes and zero running
  GPU tasks until that release is explicitly executed.
- The release requires `MN_RELEASE_ORNITH397=I_ACCEPT_2XH200`, and individual
  397B lifecycle operations require `--allow-expensive`.

## Safe operating procedure

Start from a fail-closed state:

```sh
mn stop
mn status
```

Run only the inexpensive model:

```sh
mn start fast
```

On live `v0.3.1`, do not substitute `mn/ornith-397b`; that route is not
deployed yet. After the next budgeted release, use it only with explicit
acknowledgement:

```sh
mn start ornith397 --allow-expensive
```

After the session:

```sh
mn stop fast
mn status fast
```

Inspect actual Modal usage:

```sh
.venv/bin/modal billing report \
  --for today \
  --resolution h \
  --tz local \
  --show-resources
```

`mn status` reports the desired lifecycle. The Modal dashboard/app/container
views remain the authoritative proof of running tasks and billing.

## Budget procedure

1. Open <https://modal.com/settings/usage>.
2. Select `Workspace budget`.
3. Set the lowest monthly amount the operator can afford.
4. Save and verify the displayed remaining amount.

Modal documents the Workspace budget as the hard outer monthly cap.
Environment budgets are additional compute-only guardrails and do not replace
the Workspace cap.

For future planning, the dormant 397B record represents `$9.0792/hour`,
`$0.15132/minute`, and `$0.7566` for a five-minute idle tail. If all four
source-catalog models were ever deployed simultaneously, the base GPU ceiling
would be `$20.1096/hour`, or `$1.6758` for five-minute tails. These values are
warnings, not current running costs.

## Evidence limitations

Git history proves the unsafe lifecycle code and polling behavior. Modal
billing and app/container history prove the cost totals and repeated starts.
They do not prove the exact local command responsible for every container
start, so this report does not attribute every dollar to one command.

There is no evidence that Modal failed to shut down a stable automatic session
after its configured idle interval.

Preparing a new guarded 397B route after the incident does not change this
conclusion and does not recreate the historical deployment. No deployment is
performed by the documentation or source changes alone.
