# Rewards Architecture

## Overview
The Rewards platform awards points to members for qualifying purchases. Points are
earned per transaction and can be redeemed for discounts at checkout.

## Earning
Transactions arrive on the `transactions.v1` Kafka topic and are consumed by
`TransactionConsumer`. A transaction qualifies if it is settled, not refunded, and the
member is in good standing. Members earn 1 point per dollar spent; Gold members earn 1.5x.

## Expiration
Reward points expire 365 days after the qualifying transaction.
Expiration is calculated by `RewardExpirationService.calculateExpiration()`.
A nightly batch job (`ExpirePointsJob`, 02:00 UTC) removes expired points from balances.

## API
`RewardsController` exposes:
- `GET /rewards/{memberId}/balance` — current point balance
- `GET /rewards/{memberId}/history` — earn and burn history
- `POST /rewards/{memberId}/redeem` — redeem points

## Storage
Point ledgers live in the `rewards_ledger` table in the rewards Postgres cluster.
Balances are cached in Redis with a 5 minute TTL.
