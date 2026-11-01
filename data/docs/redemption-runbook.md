# Redemption Runbook

## Symptoms of redemption failure
- `POST /rewards/{memberId}/redeem` returns 409 INSUFFICIENT_POINTS when the member has points.
- Balance shown in the app differs from the ledger.

## Checks
1. Compare Redis cached balance with the sum of `rewards_ledger` for the member.
2. If they differ, evict the cache key `balance:{memberId}`.
3. Check whether `ExpirePointsJob` ran recently; balances drop right after it runs.

## Escalation
Page the Rewards on-call via the #rewards-oncall channel.
