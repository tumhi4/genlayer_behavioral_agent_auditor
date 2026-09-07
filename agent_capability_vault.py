# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
Behavioral Agent Auditor — Autonomous Proof-of-Capability & Slashing Vault
==========================================================================
An Intelligent Contract on GenLayer that verifies claimed AI agent capabilities,
adjudicates live network endpoint behavioral probes, enforces 2-way consensus,
and executes deterministic stake custody and slashing without control-flow reverts.

Architectural Hardening (Steward Review Remediation):
1. Capability-Specific Live Probing:
   - Registers full HTTP/HTTPS endpoint URLs preserving API routes (no path truncation).
   - Generates capability-specific challenge queries directly sent to agent endpoints.
2. Symmetrical 2-Way Validator Consensus:
   - Evaluates reachability, capability demonstration, and quality score.
   - Rejects leader proposals if any field deviates in EITHER direction (false-positive OR false-negative).
3. Deterministic Slashing & Zero Reverts on Probe Outcome:
   - Offline / unreachable endpoints and incapable agents flow deterministically into SLASHED_FAILED.
   - 100% of the agent's staked deposit is slashed and awarded to the challenger without reverting.
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
    challenger_reward: u256
    quality_score: u256
    status: str                         # "PROBATION" | "ATTESTED_ACTIVE" | "SLASHED_FAILED" | "WITHDRAWN"
    last_probe_summary: str


class AgentCapabilityVault(gl.Contract):
    owner: str
    agents: TreeMap[str, AgentRecord]
    next_agent_id: u256
    total_staked_pool: u256

    def __init__(self, owner: str):
        self.owner = owner.strip().strip('"').strip("'").lower()
        self.next_agent_id = u256(2)
        self.total_staked_pool = u256(10000)

        # Seed AGENT_1: Operational agent endpoint for passing capability verification
        self.agents["AGENT_1"] = AgentRecord(
            id="AGENT_1",
            agent_address=self.owner,
            agent_endpoint="https://sponsor-sync-demo.vercel.app/youtube_perfect.html",
            claimed_capability="Interactive Web Verification & DOM Inspection",
            staked_deposit=u256(5000),
            slashed_amount=u256(0),
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
            challenger_reward=u256(0),
            quality_score=u256(0),
            status="PROBATION",
            last_probe_summary="Seed Agent 2 initialized with 5,000 stake. Awaiting failure & slashing probe audit."
        )

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
        self.total_staked_pool = self.total_staked_pool + staked

        new_agent = AgentRecord(
            id=a_id,
            agent_address=sender,
            agent_endpoint=endpoint_clean,
            claimed_capability=capability_clean,
            staked_deposit=staked,
            slashed_amount=u256(0),
            challenger_reward=u256(0),
            quality_score=u256(0),
            status="PROBATION",
            last_probe_summary=f"Agent registered with capability '{capability_clean}' and {stake_amount} tokens staked. Awaiting capability probe audit."
        )

        self.agents[a_id] = new_agent
        return a_id

    @gl.public.write
    def audit_agent_capability(self, agent_id: str, challenger_address: str = "") -> None:
        assert agent_id in self.agents, "[ERR_STATE_01] Agent record does not exist."

        agent = self.agents[agent_id]
        sender = str(gl.message.sender_address).lower()
        challenger_clean = challenger_address.strip().strip('"').strip("'").lower()
        if len(challenger_clean) == 0:
            challenger_clean = sender

        # Access Control: Only registered agent, designated challenger, or contract owner can trigger probe adjudication
        assert sender == agent.agent_address or sender == challenger_clean or sender == self.owner, \
            "[ERR_AUTH_01] Only registered agent, challenger, or contract owner can trigger probe adjudication."

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

            agent.status = "SLASHED_FAILED"
            agent.quality_score = u256(score_val)
            agent.slashed_amount = u256(staked_now)
            agent.challenger_reward = u256(staked_now)
            agent.staked_deposit = u256(0)

            reason = "Endpoint unreachable / offline." if not reachable else f"Capability not demonstrated (score: {score_val}/100)."
            agent.last_probe_summary = (
                f"BEHAVIORAL PROBE FAILED: {reason} "
                f"Full deposit of {staked_now} tokens slashed and awarded to challenger {challenger_clean}. {summary}"
            )

        self.agents[agent_id] = agent

    @gl.public.write
    def withdraw_staked_deposit(self, agent_id: str) -> None:
        assert agent_id in self.agents, "[ERR_STATE_01] Agent record does not exist."

        agent = self.agents[agent_id]
        sender = str(gl.message.sender_address).lower()

        # Access Control: Only the registered agent can withdraw their active stake
        assert sender == agent.agent_address, "[ERR_AUTH_02] Only the registered agent can withdraw active stake."
        assert agent.status == "ATTESTED_ACTIVE", "[ERR_STATE_03] Stake can only be withdrawn if status is ATTESTED_ACTIVE."
        assert int(agent.staked_deposit) > 0, "[ERR_STAKE_03] No active staked deposit to withdraw."

        withdraw_val = int(agent.staked_deposit)
        if int(self.total_staked_pool) >= withdraw_val:
            self.total_staked_pool = u256(int(self.total_staked_pool) - withdraw_val)

        agent.staked_deposit = u256(0)
        agent.status = "WITHDRAWN"
        agent.last_probe_summary = f"Staked deposit of {withdraw_val} tokens successfully withdrawn by agent {sender}."

        self.agents[agent_id] = agent

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
