# Behavioral Agent Auditor ("Proof-of-Capability")

An Intelligent Contract built on **GenLayer** for automated AI agent capability attestation, live network endpoint probing, and reputation stake slashing.

---

## 📖 How It Works

1. **Agent Registration & Staking**: An autonomous Web3 AI agent registers its claimed capability and endpoint by depositing a reputation stake (`register_agent`). State records `agent_address`, `agent_endpoint`, `claimed_capability`, `staked_deposit`, and sets status to `PROBATION`.
2. **Access Control Guardrails**: Audit execution via `audit_agent_capability` is strictly restricted to authorized participants (`agent_address`, `challenger`, or contract `owner`).
3. **Live Network Probe Audit**: GenLayer AI validators execute a live network probe directly against the agent's endpoint (`agent_endpoint`), evaluate response data, and verify capability claims.
4. **Automated Custody & Slashing Payout Execution**:
   - **Capability Passed** (`status: ATTESTED_ACTIVE`): Deposit maintained in active stake pool. Agent receives verified trust status.
   - **Capability Failed** (`status: SLASHED_FAILED`): **100% of agent deposit is slashed** (`slashed_amount`) and allocated as a bounty reward to the challenger.
5. **Stake Withdrawal**: Active attested agents can withdraw their unslashed deposit via `withdraw_staked_deposit`.

---

## 🛠️ Key Security & Technical Features

* **Real Stake Slashing Custody**: `register_agent` locks `stake_amount` into contract state (`staked_deposit` & global `total_staked_pool`).
* **Unfakeable Endpoint Probing**: Derived probe URLs construct query endpoints internally from registered agent domains (`dns.google`).
* **Substantive Validator Consensus**: Uses `gl.eq_principle.prompt_non_comparative`. Criteria require validators to independently inspect endpoint responsiveness and reject leader proposals if capability status or quality score deviates in EITHER direction.
* **Access Control Guardrails**: Restricted so only designated agents, challengers, or contract owner can initiate probe audits.

---

## 🚀 How to Test in GenLayer Studio

### 1. Deploy Contract
Deploy `AgentCapabilityVault` with your active wallet address as `owner`.

### 2. Register AI Agent
Call `register_agent`:
* `agent_endpoint`: `"google.com"`
* `claimed_capability`: `"High-Speed Network Resolution"`
* `stake_amount`: `5000`

> **Returns**: `"AGENT_1"`

### 3. Execute Behavioral Probe & Inspect Trust Status
Call `audit_agent_capability("AGENT_1")`, then call `get_agent_vault("AGENT_1")`.
