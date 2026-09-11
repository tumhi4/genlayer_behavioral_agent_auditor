# Behavioral Agent Auditor ("Proof-of-Capability & Slashing Vault")

An Intelligent Contract built on **GenLayer** for automated AI agent capability attestation, live network endpoint challenge probing, and deterministic reputation stake custody & slashing.

---

## 🌐 Live Studio Deployment & Verification

* **Contract Address:** [`0x9f2f625b2C8875c543628871ac172FEcF69Af02D`](https://explorer-studio.genlayer.com/address/0x9f2f625b2C8875c543628871ac172FEcF69Af02D)
* **Deployment Transaction:** `0x94f0da84e0ca36d6df7f5b69bdc127997ceec90a5482524197bf9a9a0aef5bec`
* **Status:** `FINALIZED` (Receipt status: 7)
* **Pre-seeded Agents:**
  - `AGENT_1`: Live operational endpoint (`https://sponsor-sync-demo.vercel.app/youtube_perfect.html`), 5,000 stake in `PROBATION`. Tests the **Passing Attestation** branch.
  - `AGENT_2`: Offline endpoint (`https://offline-unreachable-agent-node.org/api/probe`), 5,000 stake in `PROBATION`. Tests the **Deterministic Slashing & Bounty Reward** branch.

---

## 📖 How It Works

1. **Agent Registration & Deposit Custody**: An autonomous AI agent registers its claimed capability and full HTTP/HTTPS endpoint URL by locking a reputation stake (`register_agent`). State records `agent_address`, `agent_endpoint`, `claimed_capability`, credits `agent_balances`, and sets status to `PROBATION`.
2. **Permissionless Challenge Audits**: Any participant or challenger can trigger an audit via `audit_agent_capability(agent_id)`. Caller-supplied challenger addresses are eliminated; reward attribution is strictly and unforgeably bound to `gl.message.sender_address`.
3. **Live Capability Challenge Probe**: GenLayer AI consensus validators query the agent endpoint directly using a capability-specific challenge URL (`{endpoint}?challenge=verify_{agent_id}&capability={cap_slug}`) and parse the response body.
4. **Symmetrical 2-Way Validator Consensus**: Validators independently evaluate reachability, capability demonstration, and a strict quality score rubric (0, 25, 60, 100), rejecting leader proposals if any branch deviates in either direction (false-positive or false-negative).
5. **Deterministic Slashing & Zero Reverts**:
   - **Capability Passed** (`status: ATTESTED_ACTIVE`): Deposit is maintained in active stake pool. Agent is certified.
   - **Capability Failed / Unreachable** (`status: SLASHED_FAILED`): **100% of agent deposit is slashed** without reverting transactions. Slashed funds are debited from `agent_balances` and credited to `claimable_rewards[challenger_address]`.
6. **Enforceable Stake Withdrawal**: Attested agents (`status: ATTESTED_ACTIVE`) can withdraw their unslashed deposit via `withdraw_staked_deposit(agent_id)`, strictly restricted to the registered `agent_address`.
7. **Enforceable Challenger Bounty Claim**: Challengers can claim accumulated slashing rewards via `claim_challenger_reward()`, strictly bound to `gl.message.sender_address`.

---

## 🛡️ Architectural Hardening (Steward Review Remediation)

| Feedback / Prior Limitation | Hardened Implementation (Joaquin - Sep 11) |
|---|---|
| **Caller-supplied challenger address** | Removed `challenger_address` parameter from `audit_agent_capability`. Audits are explicitly permissionless and the challenger is strictly bound to `gl.message.sender_address`. |
| **Missing stake custody & withdrawal** | Implemented `agent_balances: TreeMap[str, u256]`. Attested agents (`ATTESTED_ACTIVE`) withdraw active stake via `withdraw_staked_deposit` restricted to `agent_address`. |
| **Non-enforceable slashing rewards** | Implemented `claimable_rewards: TreeMap[str, u256]`. When an agent fails audit, 100% deposit is credited to the caller, claimable via `claim_challenger_reward()`. |
| **DNS-only resolution (`dns.google`)** | Replaced with direct endpoint queries preserving full URL routes and querying capability challenges. |
| **Path truncation (`split('/')[0]`)** | Removed all domain stripping. Full endpoints with routes and query params are fully preserved. |
| **Asymmetric / Unbound validator criteria** | Enforced 2-way symmetrical criteria: leader proposals are rejected if reachability, capability, or score deviate in EITHER direction. |
| **Control-flow revert (`assert reachable == True`)** | Removed revert assertion. Unreachable/error endpoints flow deterministically into `SLASHED_FAILED` with 100% stake slashed to the challenger. |

---

## 🚀 How to Test in GenLayer Studio

### 1. View Contract State
Navigate to [`0x9f2f625b2C8875c543628871ac172FEcF69Af02D`](https://explorer-studio.genlayer.com/address/0x9f2f625b2C8875c543628871ac172FEcF69Af02D):
* Call `get_total_agents()` -> returns `2`
* Call `get_staked_pool_balance()` -> returns `10000`
* Call `get_agent_vault("AGENT_1")` -> returns `AGENT_1` in `PROBATION` with 5,000 stake
* Call `get_agent_vault("AGENT_2")` -> returns `AGENT_2` in `PROBATION` with 5,000 stake

### 2. Test Passing Capability Attestation
Call `audit_agent_capability("AGENT_1")`:
* The contract queries `https://sponsor-sync-demo.vercel.app/youtube_perfect.html?challenge=verify_AGENT_1&capability=Interactive_Web_Verification_&_DOM_Inspection`.
* Validators reach consensus: `endpoint_reachable: true`, `capability_passed: true`, `quality_score: 100`.
* State updates: `status: ATTESTED_ACTIVE`, stake preserved in pool.
* Agent can call `withdraw_staked_deposit("AGENT_1")` to withdraw active deposit.

### 3. Test Deterministic Slashing (Zero Reverts) & Claim Bounty
Call `audit_agent_capability("AGENT_2")`:
* The contract probes offline endpoint `https://offline-unreachable-agent-node.org/api/probe`.
* Validators reach consensus: `endpoint_reachable: false`, `capability_passed: false`, `quality_score: 0`.
* Deterministic execution: **Zero revert**. Status updates to `SLASHED_FAILED`.
* 5,000 stake slashed from pool and credited to `claimable_rewards[caller]`.
* Challenger calls `claim_challenger_reward()` -> receives 5,000 bounty!

### 4. Register a New Custom Agent
Call `register_agent`:
* `endpoint`: `"https://my-agent.io/api/v1/verify"`
* `capability`: `"Natural Language Contract Analysis"`
* `stake_amount`: `2500`
* Returns: `"AGENT_3"`
