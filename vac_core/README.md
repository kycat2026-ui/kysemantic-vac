# VAC Authorization Core (prototype)

This is the first executable authorization boundary for VAC. It is deliberately
separate from the existing Shitocat and Godseal deployments.

## Decision rule

A request is allowed only if a grant exists and exactly matches:
- data owner
- requesting subject / agent
- resource identifier
- declared purpose
- active time window

Revoked, expired, incomplete, malformed, or mismatched grants are denied.
No grant means deny. This is a decision engine, not yet a production gateway.

## Run tests

From the repository root:

```sh
python -m unittest discover -s vac_core -p 'test_*.py' -v
```

## Important boundary

The caller must authenticate the subject and obtain grant records from a trusted
store. Never trust owner_id or subject_id supplied directly by an untrusted
client. The caller must enforce the decision before retrieving or returning data.
Do not put private user data or secrets on-chain. Database RLS remains mandatory.
