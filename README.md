# Behavioral Agent Auditor ("Proof-of-Capability & Slashing Vault")

An Intelligent Contract built on **GenLayer** for automated AI agent capability attestation, live network endpoint challenge probing, and deterministic reputation stake slashing.

---

## 🌐 Live Studio Deployment & Verification

* **Contract Address:** [`0x29612DFC32dEf741c1120fbfBb5dB8aD758A8441`](https://explorer-studio.genlayer.com/address/0x29612DFC32dEf741c1120fbfBb5dB8aD758A8441)
* **Deployment Transaction:** `0x44b71f18a3dfc8dc0192315dce33bc018b9862b889f857bceb32e638e2f69636`
* **Status:** `FINALIZED` (Receipt status: 7)
* **Pre-seeded Agents:**
  - `AGENT_1`: Live endpoint (`https://sponsor-sync-demo.vercel.app/youtube_perfect.html`), 5,000 stake in `PROBATION`. Tests the **Passing Attestation** branch.
  - `AGENT_2`: Offline endpoint (`https://offline-unreachable-agent-node.org/api/probe`), 5,000 stake in `PROBATION`. Tests the **Deterministic Slashing & Bounty Reward** branch.

---

## 📖 How It Works

1. **Agent Registration & Staking**: An autonomous AI agent registers its claimed capability and full HTTP/HTTPS endpoint URL by locking a reputation stake (`register_agent`). State records `agent_address`, `agent_endpoint`, `claimed_capability`, and sets status to `PROBATION`.
2. **Access Control Guardrails**: Audit execution via `audit_agent_capability` is strictly restricted to authorized participants (`agent_address`, designated `challenger`, or contract `owner`).
3. **Live Capability Challenge Probe**: GenLayer AI consensus validators query the agent endpoint directly using a capability-specific challenge URL (`{endpoint}?challenge=verify_{agent_id}&capability={cap_slug}`) and parse the response body.
4. **Symmetrical 2-Way Validator Consensus**: Validators independently evaluate reachability, capability demonstration, and a strict quality score rubric (0, 25, 60, 100), rejecting leader proposals if any branch deviates in either direction (false-positive or false-negative).
5. **Deterministic Slashing Payout & Zero Reverts**:
   - **Capability Passed** (`status: ATTESTED_ACTIVE`): Deposit maintained in active stake pool. Agent is certified.
   - **Capability Failed / Unreachable** (`status: SLASHED_FAILED`): **100% of agent deposit is slashed** without reverting transactions, immediately credited to the challenger.
6. **Stake Withdrawal**: Active attested agents can withdraw their unslashed deposit via `withdraw_staked_deposit`.

---

## 🛡️ Architectural Hardening (Steward Review Remediation)

| Previous Issue | Hardened Implementation |
|---|---|
| **DNS-only resolution (`dns.google`)** | Replaced with direct endpoint queries preserving full URL routes and querying capability challenges. |
| **Path truncation (`split('/')[0]`)** | Removed all domain stripping. Full endpoints with routes and query params are fully preserved. |
| **Asymmetric / Unbound validator criteria** | Enforced 2-way symmetrical criteria: leader proposals are rejected if reachability, capability, or score deviate in EITHER direction. |
| **Control-flow revert (`assert reachable == True`)** | Removed revert assertion. Unreachable/error endpoints flow deterministically into `SLASHED_FAILED` with 100% stake slashed to the challenger. |

---

## 🚀 How to Test in GenLayer Studio

### 1. View Contract State
Navigate to [`0x29612DFC32dEf741c1120fbfBb5dB8aD758A8441`](https://explorer-studio.genlayer.com/address/0x29612DFC32dEf741c1120fbfBb5dB8aD758A8441):
* Call `get_total_agents()` -> returns `2`
* Call `get_staked_pool_balance()` -> returns `10000`
* Call `get_agent_vault("AGENT_1")` -> returns `AGENT_1` in `PROBATION` with 5,000 stake

### 2. Test Passing Capability Attestation
Call `audit_agent_capability("AGENT_1")`:
* The contract queries `https://sponsor-sync-demo.vercel.app/youtube_perfect.html?challenge=verify_AGENT_1&capability=Interactive_Web_Verification_&_DOM_Inspection`.
* Validators reach consensus: `endpoint_reachable: true`, `capability_passed: true`, `quality_score: 100`.
* State updates: `status: ATTESTED_ACTIVE`, stake preserved in pool.

### 3. Test Deterministic Slashing (Zero Reverts)
Call `audit_agent_capability("AGENT_2")`:
* The contract probes offline endpoint `https://offline-unreachable-agent-node.org/api/probe`.
* Validators reach consensus: `endpoint_reachable: false`, `capability_passed: false`, `quality_score: 0`.
* Deterministic execution: **Zero revert**. Status updates to `SLASHED_FAILED`.
* 5,000 stake slashed from pool and awarded to challenger.

### 4. Register a New Custom Agent
Call `register_agent`:
* `agent_endpoint`: `"https://my-agent.io/api/v1/verify"`
* `claimed_capability`: `"Natural Language Contract Analysis"`
* `stake_amount`: `2500`
* Returns: `"AGENT_3"`
