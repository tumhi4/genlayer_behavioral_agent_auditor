CHANGES MADE (Per Joaquin's Steward Review):

1. Permissionless Audits & Caller Attribution:
- Removed caller-supplied challenger_address from audit_agent_capability(agent_id).
- Audits are explicitly permissionless: anyone can call, and challenger attribution is strictly bound to gl.message.sender_address, preventing caller spoofing.

2. Stake Custody & Entitled Address Withdrawal:
- Added agent_balances: TreeMap[str, u256] tracking active deposited stake.
- Enforceable withdrawal: withdraw_staked_deposit(agent_id) is strictly restricted to agent.agent_address when ATTESTED_ACTIVE.

3. Enforceable Slashing Bounty Claim Path:
- Added claimable_rewards: TreeMap[str, u256]. Slashed stake credits the challenger caller directly.
- Challengers claim bounties via claim_challenger_reward(), bound strictly to msg.sender.

Studio Contract: 0x9f2f625b2C8875c543628871ac172FEcF69Af02D
Pre-seeded: AGENT_1 (attestation), AGENT_2 (slashing)