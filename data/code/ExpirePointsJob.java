package com.acme.rewards.expiration;

import java.time.LocalDate;
import org.springframework.scheduling.annotation.Scheduled;

public class ExpirePointsJob {

    private final RewardsLedger ledger;
    private final RewardExpirationService expirationService;

    public ExpirePointsJob(RewardsLedger ledger, RewardExpirationService expirationService) {
        this.ledger = ledger;
        this.expirationService = expirationService;
    }

    // Runs nightly at 02:00 UTC
    @Scheduled(cron = "0 0 2 * * *", zone = "UTC")
    public void expirePoints() {
        LocalDate today = LocalDate.now();
        for (LedgerEntry entry : ledger.findUnexpiredEarnEntries()) {
            if (expirationService.isExpired(entry.transactionDate(), today)) {
                ledger.expire(entry);
            }
        }
    }
}
