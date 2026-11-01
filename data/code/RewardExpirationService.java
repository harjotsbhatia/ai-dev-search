package com.acme.rewards.expiration;

import java.time.LocalDate;

/**
 * Calculates when reward points expire.
 * Policy: points expire 365 days after the qualifying transaction.
 */
public class RewardExpirationService {

    static final int EXPIRATION_DAYS = 365;

    public LocalDate calculateExpiration(LocalDate transactionDate) {
        return transactionDate.plusDays(EXPIRATION_DAYS);
    }

    public boolean isExpired(LocalDate transactionDate, LocalDate today) {
        return !today.isBefore(calculateExpiration(transactionDate));
    }
}
