# Membership Architecture

## Overview
The Membership service owns member profiles, tiers, and account status.

## Tiers
- Standard: default tier on sign-up.
- Gold: members who spend more than $5,000 in a rolling 12-month window.
Tier recalculation runs weekly via `TierRecalculationJob` on Sundays at 03:00 UTC.

## Account status
A member can be ACTIVE, SUSPENDED, or CLOSED. Suspended members do not earn rewards.
Closing an account forfeits all unredeemed reward points.

## Integration with Rewards
The Rewards platform calls `GET /members/{memberId}` to look up tier and status when
processing a transaction. Responses are cached for 10 minutes.
