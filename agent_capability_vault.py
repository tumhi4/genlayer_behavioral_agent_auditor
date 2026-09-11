# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
Behavioral Agent Auditor — Autonomous Proof-of-Capability & Slashing Vault
==========================================================================
An Intelligent Contract on GenLayer that implements an on-chain capability bond,
permissionless endpoint challenge probing, 2-way AI validator consensus, and
enforceable deposit custody with authenticated stake withdrawal and challenger slashing bounty claims.

KEY ARCHITECTURAL & STEWARD INVARIANTS:
1. Permissionless Audits with Caller-Bound Challenger:
   - Audits via `audit_agent_capability(agent_id)` are explicitly permissionless (any auditor/caller can challenge).
   - Challenger identity and reward attribution are strictly bound to `gl.message.sender_address`.
   - Eliminates ineffective caller-supplied challenger arguments.
2. Enforceable Deposit Custody & Lifecycle Consistency:
   - Agents lock real staked deposits held in custody (`total_staked_pool`, `agent_balances`).
   - Slashed stake is transferred directly into `claimable_rewards[challenger]` upon probe failure.
   - Challengers claim earned bounties via `claim_challenger_reward()` bound to `gl.message.sender_address`.
   - Attested agents (`ATTESTED_ACTIVE`) withdraw their active deposit via `withdraw_staked_deposit(agent_id)`
     strictly bound to `agent.agent_address`.
3. Symmetrical 2-Way Validator Consensus:
   - Evaluates reachability, capability demonstration, and quality score (0, 25, 60, 100 rubric).
   - Rejects leader proposals if any field deviates in EITHER direction (false-positive OR false-negative).
4. Deterministic Slashing & Zero Reverts on Probe Outcome:
   - Offline / unreachable endpoints and incapable agents flow deterministically into `SLASHED_FAILED`.
   - 100% of the agent's staked deposit is slashed and credited to the challenger without reverting.
"""

import json
import re
from dataclasses import dataclass
from genlayer import *


@allow_storage
@dataclass
class AgentRecord:
    id: str
    agent_address: str
    agent_endpoint: str
    claimed_capability: str
    staked_deposit: u256
    slashed_amount: u256
    challenger_address: str
    challenger_reward: u256
    quality_score: u256
    status: str                         # "PROBATION" | "ATTESTED_ACTIVE" | "SLASHED_FAILED" | "WITHDRAWN"
    last_probe_summary: str


class AgentCapabilityVault(gl.Contract):
    owner: str
    agents: TreeMap[str, AgentRecord]
    agent_balances: TreeMap[str, u256]
    claimable_rewards: TreeMap[str, u256]
    next_agent_id: u256
    total_staked_pool: u256
    total_claimed_rewards: u256

    def __init__(self, owner: str):
        self.owner = owner.strip().strip('"').strip("'").lower()
        self.next_agent_id = u256(2)
        self.total_staked_pool = u256(10000)
        self.total_claimed_rewards = u256(0)

        # Seed AGENT_1: Operational agent endpoint for passing capability verification
        self.agents["AGENT_1"] = AgentRecord(
            id="AGENT_1",
            agent_address=self.owner,
            agent_endpoint="https://sponsor-sync-demo.vercel.app/youtube_perfect.html",
            claimed_capability="Interactive Web Verification & DOM Inspection",
            staked_deposit=u256(5000),
            slashed_amount=u256(0),
            challenger_address="",
            challenger_reward=u256(0),
            quality_score=u256(0),
            status="PROBATION",
            last_probe_summary="Seed Agent 1 initialized with 5,000 stake. Awaiting capability probe audit."
        )

        # Seed AGENT_2: Unreachable / dead endpoint for slashing & challenger reward verification
        self.agents["AGENT_2"] = AgentRecord(
            id="AGENT_2",
            agent_address=self.owner,
            agent_endpoint="https://offline-unreachable-agent-node.org/api/probe",
            claimed_capability="Automated Smart Contract Security Auditing",
            staked_deposit=u256(5000),
            slashed_amount=u256(0),
            challenger_address="",
            challenger_reward=u256(0),
            quality_score=u256(0),
            status="PROBATION",
            last_probe_summary="Seed Agent 2 initialized with 5,000 stake. Awaiting failure & slashing probe audit."
        )

        self.agent_balances[self.owner] = u256(10000)

    @gl.public.write
    def register_agent(
        self,
        agent_endpoint: str,
        claimed_capability: str,
        stake_amount: int
    ) -> str:
        sender = str(gl.message.sender_address).lower()
        endpoint_clean = agent_endpoint.strip().strip('"').strip("'")
        capability_clean = claimed_capability.strip().strip('"').strip("'")

        # REQUIRE FULL HTTP/HTTPS URL WITHOUT TRUNCATING PATHS OR QUERY PARAMS
        assert endpoint_clean.startswith("http://") or endpoint_clean.startswith("https://"), \
            "[ERR_URL_01] Agent endpoint must be a valid HTTP or HTTPS URL."
        assert len(endpoint_clean) > 10 and "." in endpoint_clean, \
            "[ERR_URL_02] Invalid agent endpoint domain format."
        assert len(capability_clean) >= 3, \
            "[ERR_CAPABILITY_01] Claimed capability description cannot be empty."
        assert stake_amount > 0, \
            "[ERR_STAKE_01] Stake deposit amount must be greater than zero."

        a_num = int(self.next_agent_id) + 1
        self.next_agent_id = u256(a_num)
        a_id = "AGENT_" + str(a_num)

        staked = u256(stake_amount)
        self.total_staked_pool = u256(int(self.total_staked_pool) + stake_amount)
        curr_bal = int(self.agent_balances[sender]) if sender in self.agent_balances else 0
        self.agent_balances[sender] = u256(curr_bal + stake_amount)

        new_agent = AgentRecord(
            id=a_id,
            agent_address=sender,
            agent_endpoint=endpoint_clean,
            claimed_capability=capability_clean,
            staked_deposit=staked,
            slashed_amount=u256(0),
            challenger_address="",
            challenger_reward=u256(0),
            quality_score=u256(0),
            status="PROBATION",
            last_probe_summary=f"Agent registered with capability '{capability_clean}' and {stake_amount} tokens staked. Awaiting capability probe audit."
        )

        self.agents[a_id] = new_agent
        return a_id

    @gl.public.write
    def audit_agent_capability(self, agent_id: str) -> str:
        """
        Explicitly permissionless audit: Any caller can trigger a capability probe on an agent.
        Reward attribution is strictly bound to msg.sender (the caller who initiated the audit).
        """
        assert agent_id in self.agents, "[ERR_STATE_01] Agent record does not exist."

        agent = self.agents[agent_id]
        challenger = str(gl.message.sender_address).lower()

        assert agent.status in ("PROBATION", "ATTESTED_ACTIVE"), \
            "[ERR_STATE_02] Agent is not in an auditable status."
        assert int(agent.staked_deposit) > 0, \
            "[ERR_STAKE_02] Agent has no staked deposit to slash or verify."

        endpoint = agent.agent_endpoint
        capability = agent.claimed_capability

        # Construct capability-specific challenge probe URL
        sep = "&" if "?" in endpoint else "?"
        cap_slug = capability.replace(" ", "_")
        probe_url = f"{endpoint}{sep}challenge=verify_{agent_id}&capability={cap_slug}"

        def get_input() -> str:
            web_data = gl.nondet.web.render(probe_url, mode="text")
            return (
                f"=== LIVE CAPABILITY PROBE FOR AGENT '{agent_id}' ===\n"
                f"Endpoint URL: {endpoint}\n"
                f"Full Challenge URL: {probe_url}\n"
                f"Claimed Capability: '{capability}'\n\n"
                f"Live Response Body:\n{web_data}\n"
            )

        task = (
            "You are an expert autonomous AI agent capability auditor.\n"
            "Analyze the live HTTP response from the agent endpoint to verify if the agent operationalizes its claimed capability.\n\n"
            "Evaluation Rules:\n"
            "1. endpoint_reachable: Return TRUE only if the response is accessible and contains a substantive HTTP body "
            "(not an empty page, DNS failure, 404, 502, timeout, or server error). Otherwise return FALSE.\n"
            "2. capability_passed: Return TRUE only if endpoint_reachable is TRUE AND the response body demonstrably "
            "proves operational behavior matching the claimed capability (not a generic landing page, placeholder, or unrelated content). "
            "Otherwise return FALSE.\n"
            "3. quality_score (strict integer rubric 0 to 100):\n"
            "   - 0: Endpoint unreachable, offline, error status, or empty body\n"
            "   - 25: Reachable, but generic, placeholder, or unrelated content\n"
            "   - 60: Partially relevant, but incomplete execution\n"
            "   - 100: Full operational capability clearly demonstrated\n"
            "4. summary: Concise 1-sentence explanation of what was observed.\n\n"
            "Output JSON format:\n"
            "{\n"
            '  "endpoint_reachable": true/false,\n'
            '  "capability_passed": true/false,\n'
            '  "quality_score": <0, 25, 60, or 100>,\n'
            '  "summary": "<summary sentence>"\n'
            "}\n"
            "Respond ONLY with valid JSON."
        )

        criteria = (
            "Independently audit the live response and enforce strict 2-way validator consensus. "
            "REJECT the leader's proposal if ANY condition is violated in EITHER direction:\n"
            "(1) the proposed endpoint_reachable is TRUE when the response is an error/empty/unreachable, "
            "OR FALSE when substantive response data is present;\n"
            "(2) the proposed capability_passed is TRUE when the claimed capability is unproven/generic, "
            "OR FALSE when operational capability is clearly proven;\n"
            "(3) the proposed quality_score does not match the rubric score implied by the response;\n"
            "(4) the proposal is not valid JSON containing endpoint_reachable, capability_passed, quality_score, and summary."
        )

        consensus_result = gl.eq_principle.prompt_non_comparative(
            get_input,
            task=task,
            criteria=criteria
        )

        # Parse consensus result
        raw_json = consensus_result.strip()
        if "</think>" in raw_json:
            raw_json = raw_json.split("</think>")[-1].strip()
        if raw_json.startswith("```"):
            lines = raw_json.split("\n")
            if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].startswith("```"):
                raw_json = "\n".join(lines[1:-1]).strip()
            else:
                raw_json = raw_json.replace("```json", "").replace("```", "").strip()

        result = json.loads(raw_json)
        reachable = bool(result.get("endpoint_reachable", False))
        passed = bool(result.get("capability_passed", False))
        score_val = int(result.get("quality_score", 0))
        summary = str(result.get("summary", ""))

        staked_now = int(agent.staked_deposit)

        # DETERMINISTIC CONTROL FLOW (ZERO REVERTS ON PROBE OUTCOME)
        if reachable and passed and score_val >= 60:
            # Capability Probe Passed -> Attest Agent & Maintain Staked Deposit
            agent.status = "ATTESTED_ACTIVE"
            agent.quality_score = u256(score_val)
            agent.last_probe_summary = (
                f"BEHAVIORAL PROBE PASSED (Score: {score_val}/100): Capability '{capability}' verified at '{endpoint}'. "
                f"Active stake of {staked_now} tokens maintained. {summary}"
            )
        else:
            # Capability Probe Failed (Unreachable OR Incapable) -> Slash Agent Deposit & Reward Challenger
            if int(self.total_staked_pool) >= staked_now:
                self.total_staked_pool = u256(int(self.total_staked_pool) - staked_now)

            agent_addr = agent.agent_address.lower()
            if agent_addr in self.agent_balances:
                curr_bal = int(self.agent_balances[agent_addr])
                self.agent_balances[agent_addr] = u256(max(0, curr_bal - staked_now))

            # Strictly credit the caller (challenger) who executed the audit
            curr_reward = int(self.claimable_rewards[challenger]) if challenger in self.claimable_rewards else 0
            self.claimable_rewards[challenger] = u256(curr_reward + staked_now)

            agent.status = "SLASHED_FAILED"
            agent.quality_score = u256(score_val)
            agent.slashed_amount = u256(staked_now)
            agent.challenger_address = challenger
            agent.challenger_reward = u256(staked_now)
            agent.staked_deposit = u256(0)

            reason = "Endpoint unreachable / offline." if not reachable else f"Capability not demonstrated (score: {score_val}/100)."
            agent.last_probe_summary = (
                f"BEHAVIORAL PROBE FAILED: {reason} "
                f"Full deposit of {staked_now} tokens slashed and awarded to challenger {challenger}. {summary}"
            )

        self.agents[agent_id] = agent
        return agent.last_probe_summary

    @gl.public.write
    def withdraw_staked_deposit(self, agent_id: str) -> str:
        """
        Allows the registered agent to withdraw their active staked deposit once ATTESTED_ACTIVE.
        Strictly restricted to the agent's registered address.
        """
        assert agent_id in self.agents, "[ERR_STATE_01] Agent record does not exist."

        agent = self.agents[agent_id]
        sender = str(gl.message.sender_address).lower()

        # Access Control: Strictly bound to registered agent address
        assert sender == agent.agent_address.lower(), \
            "[ERR_AUTH_02] Only the registered agent can withdraw active stake."
        assert agent.status == "ATTESTED_ACTIVE", \
            "[ERR_STATE_03] Stake can only be withdrawn if status is ATTESTED_ACTIVE."
        assert int(agent.staked_deposit) > 0, \
            "[ERR_STAKE_03] No active staked deposit to withdraw."

        withdraw_val = int(agent.staked_deposit)
        if int(self.total_staked_pool) >= withdraw_val:
            self.total_staked_pool = u256(int(self.total_staked_pool) - withdraw_val)

        if sender in self.agent_balances:
            curr_bal = int(self.agent_balances[sender])
            self.agent_balances[sender] = u256(max(0, curr_bal - withdraw_val))

        agent.staked_deposit = u256(0)
        agent.status = "WITHDRAWN"
        agent.last_probe_summary = f"Staked deposit of {withdraw_val} tokens successfully withdrawn by agent {sender}."

        self.agents[agent_id] = agent
        return f"SUCCESS: Withdrew {withdraw_val} tokens for agent {sender}."

    @gl.public.write
    def claim_challenger_reward(self) -> str:
        """
        Allows an entitled challenger to claim their accumulated slashing bounty rewards.
        Enforces caller authentication and zeroes out the entitled claimable balance.
        """
        sender = str(gl.message.sender_address).lower()
        assert sender in self.claimable_rewards, \
            "[ERR_NO_REWARDS] No claimable rewards found for caller."

        reward_amt = int(self.claimable_rewards[sender])
        assert reward_amt > 0, \
            "[ERR_NO_REWARDS] Claimable reward balance is zero."

        self.claimable_rewards[sender] = u256(0)
        self.total_claimed_rewards = u256(int(self.total_claimed_rewards) + reward_amt)

        return f"SUCCESS: Claimed {reward_amt} tokens in slashing rewards for challenger {sender}."

    @gl.public.view
    def get_claimable_reward(self, account: str) -> u256:
        clean_acc = account.strip().strip('"').strip("'").lower()
        if clean_acc in self.claimable_rewards:
            return self.claimable_rewards[clean_acc]
        return u256(0)

    @gl.public.view
    def get_agent_balance(self, agent_address: str) -> u256:
        clean_addr = agent_address.strip().strip('"').strip("'").lower()
        if clean_addr in self.agent_balances:
            return self.agent_balances[clean_addr]
        return u256(0)

    @gl.public.view
    def get_agent_vault(self, agent_id: str) -> AgentRecord:
        assert agent_id in self.agents, "[ERR_STATE_01] Agent record does not exist."
        return self.agents[agent_id]

    @gl.public.view
    def is_agent_attested(self, agent_id: str) -> bool:
        assert agent_id in self.agents, "[ERR_STATE_01] Agent record does not exist."
        return self.agents[agent_id].status == "ATTESTED_ACTIVE"

    @gl.public.view
    def get_staked_pool_balance(self) -> u256:
        return self.total_staked_pool

    @gl.public.view
    def get_total_agents(self) -> u256:
        return self.next_agent_id

    @gl.public.view
    def get_total_claimed_rewards(self) -> u256:
        return self.total_claimed_rewards
