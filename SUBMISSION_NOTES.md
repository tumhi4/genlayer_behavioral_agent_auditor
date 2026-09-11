Behavioral Agent Auditor (Proof-of-Capability Vault)
Decentralized capability attestation & stake vault for Web3 AI agents on GenLayer.

Steward Feedback Addressed (Joaquin - Sep 11):
1. Permissionless Audits: audit_agent_capability(agent_id) is permissionless. Challenger attribution is unforgeably bound to gl.message.sender_address (caller-supplied challenger parameter removed).
2. Stake Custody & Withdrawal: Active deposits are tracked in agent_balances. Attested agents withdraw active stake via withdraw_staked_deposit(agent_id) restricted strictly to agent_address.
3. Enforceable Slashing Rewards: Slashed stake credits claimable_rewards[challenger]. Entitled challengers withdraw bounties via claim_challenger_reward().
4. Zero-Revert Slashing: Offline or failing endpoints deterministically slash 100% deposit to the challenger.

Studio Deployment: 0x9f2f625b2C8875c543628871ac172FEcF69Af02D
Pre-seeded: AGENT_1 (attestation), AGENT_2 (slashing)