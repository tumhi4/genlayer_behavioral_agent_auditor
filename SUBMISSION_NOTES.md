Behavioral Agent Auditor (Proof-of-Capability Vault)

Autonomous AI agent capability attestation, live endpoint probing, and deterministic stake slashing on GenLayer.

1. Registration & Stake: Agents register capabilities and full HTTP/HTTPS URLs by depositing reputation stake (staked_deposit).
2. Live Probing: Validators query agent endpoints with capability challenges ({endpoint}?challenge=verify_{agent_id}&capability={cap_slug}) and audit live responses.
3. Symmetrical Consensus: Validators enforce 2-way consensus across reachability, capability, and score (0/25/60/100 rubric), rejecting deviations in EITHER direction.
4. Deterministic Slashing: Offline or incapable agents transition to SLASHED_FAILED, slashing 100% stake to challenger with zero reverts. Certified agents reach ATTESTED_ACTIVE.

Studio Verification (0x29612DFC32dEf741c1120fbfBb5dB8aD758A8441):
- AGENT_1: Passing probe -> ATTESTED_ACTIVE (score 100)
- AGENT_2: Offline probe -> SLASHED_FAILED (5k stake slashed)