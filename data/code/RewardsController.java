package com.acme.rewards.api;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/rewards")
public class RewardsController {

    private final RewardsService rewardsService;

    public RewardsController(RewardsService rewardsService) {
        this.rewardsService = rewardsService;
    }

    @GetMapping("/{memberId}/balance")
    public BalanceResponse getBalance(@PathVariable String memberId) {
        return rewardsService.getBalance(memberId);
    }

    @GetMapping("/{memberId}/history")
    public HistoryResponse getHistory(@PathVariable String memberId) {
        return rewardsService.getHistory(memberId);
    }

    @PostMapping("/{memberId}/redeem")
    public RedeemResponse redeem(@PathVariable String memberId, @RequestBody RedeemRequest request) {
        if (request.points() <= 0) {
            throw new IllegalArgumentException("points must be positive");
        }
        return rewardsService.redeem(memberId, request.points());
    }
}
