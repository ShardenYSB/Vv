"""Referral reward rules, loaded from DB settings by the application layer."""
from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class RewardRange: lower: int; upper: int; stars: int
DEFAULT_REWARD_RANGES = (RewardRange(3,5,1), RewardRange(6,8,2), RewardRange(9,15,3), RewardRange(16,20,5))
def get_referral_reward(sponsors_count: int, ranges: tuple[RewardRange, ...] = DEFAULT_REWARD_RANGES) -> int:
    return next((item.stars for item in ranges if item.lower <= sponsors_count <= item.upper), 0)
