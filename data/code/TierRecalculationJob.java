package com.acme.membership.tiers;

import java.math.BigDecimal;
import org.springframework.scheduling.annotation.Scheduled;

public class TierRecalculationJob {

    static final BigDecimal GOLD_THRESHOLD = new BigDecimal("5000");

    private final MemberRepository members;
    private final SpendRepository spend;

    public TierRecalculationJob(MemberRepository members, SpendRepository spend) {
        this.members = members;
        this.spend = spend;
    }

    // Sundays at 03:00 UTC
    @Scheduled(cron = "0 0 3 * * SUN", zone = "UTC")
    public void recalculate() {
        for (Member m : members.findAllActive()) {
            BigDecimal last12Months = spend.totalForLast12Months(m.id());
            Tier tier = last12Months.compareTo(GOLD_THRESHOLD) > 0 ? Tier.GOLD : Tier.STANDARD;
            members.updateTier(m.id(), tier);
        }
    }
}
