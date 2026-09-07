Remediated per steward review on capability evidence & validator binding:

1. Capability-Specific Live Evidence: Purged DNS TXT queries. Full HTTP/HTTPS URLs are preserved with complete route paths. Validators query live agent endpoints with challenge queries ({endpoint}?challenge=verify_{agent_id}&capability={cap_slug}) and verify response bodies against claimed capabilities.
2. Symmetrical 2-Way Validator Binding: Reachability, capability, and score (0/25/60/100 rubric) are bound in both directions. Validators reject proposals if reachability or capability deviates in either direction.
3. Zero-Revert Deterministic Slashing: Purged assert reachable == True. Offline and incapable agents deterministically transition to SLASHED_FAILED, slashing 100% stake to challenger with zero reverts.

Studio Deployment: 0x29612DFC32dEf741c1120fbfBb5dB8aD758A8441
Pre-seeded for instant verification:
- AGENT_1: Passing attestation
- AGENT_2: Slashing & bounty payout