Behavioral Agent Auditor (Proof-of-Capability Vault)
Decentralized reputation and attestation registry for autonomous Web3 AI agents on GenLayer.

Core Lifecycle:
1. Stake & Registration: AI agents lock reputation stake (staked_deposit) and register full HTTP/HTTPS URLs.
2. Live Challenge Probing: Validators query agent endpoints directly ({endpoint}?challenge=verify_{agent_id}&capability={cap_slug}) to audit live response bodies.
3. 2-Way Symmetrical Consensus: 2-way Equivalence Principle binding on reachability, capability, and score (0/25/60/100 rubric), rejecting deviations in either direction.
4. Deterministic Slashing (Zero Reverts): Offline or incapable agents transition to SLASHED_FAILED, slashing 100% stake to challenger with zero reverts. Attested agents reach ATTESTED_ACTIVE.

Studio Deployment: 0x29612DFC32dEf741c1120fbfBb5dB8aD758A8441
Pre-seeded for Instant Review:
- AGENT_1: Passing attestation probe
- AGENT_2: Offline slashing & bounty