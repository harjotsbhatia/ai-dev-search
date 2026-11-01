package com.acme.rewards.ingest;

import org.springframework.kafka.annotation.KafkaListener;

public class TransactionConsumer {

    private final RewardsLedger ledger;
    private final MembershipClient membershipClient;

    public TransactionConsumer(RewardsLedger ledger, MembershipClient membershipClient) {
        this.ledger = ledger;
        this.membershipClient = membershipClient;
    }

    @KafkaListener(topics = "transactions.v1")
    public void onTransaction(TransactionEvent event) {
        // Idempotency check added after INC-102
        if (ledger.containsTransaction(event.transactionId())) {
            return;
        }
        if (!event.settled() || event.refunded()) {
            return;
        }
        Member member = membershipClient.getMember(event.memberId());
        if (member.status() != MemberStatus.ACTIVE) {
            return;
        }
        double multiplier = member.tier() == Tier.GOLD ? 1.5 : 1.0;
        long points = Math.round(event.amountDollars() * multiplier);
        ledger.award(event.memberId(), event.transactionId(), points, event.transactionDate());
    }
}
