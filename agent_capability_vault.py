# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
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
    status: str
    last_probe_summary: str


class AgentCapabilityVault(gl.Contract):
    owner: str
    agents: TreeMap[str, AgentRecord]
    next_agent_id: u256
    total_staked_pool: u256

    def __init__(self, owner: str):
        self.owner = owner.lower()
        # GenLayer VM automatically instantiates storage-backed TreeMaps.
        # We must never assign TreeMap() manually in the constructor.
        self.next_agent_id = u256(0)
        self.total_staked_pool = u256(0)

    @gl.public.write
    def register_agent(
        self,
        agent_endpoint: str,
        claimed_capability: str,
        stake_amount: int
    ) -> str:
        sender = str(gl.message.sender_address).lower()
        endpoint_clean = agent_endpoint.strip().strip('"').strip("'").lower()
        capability_clean = claimed_capability.strip().strip('"').strip("'")

        # Sanitize endpoint removing protocol prefixes if present
        if endpoint_clean.startswith("https://"):
            endpoint_clean = endpoint_clean[8:]
        elif endpoint_clean.startswith("http://"):
            endpoint_clean = endpoint_clean[7:]
        endpoint_clean = endpoint_clean.split("/")[0].strip()

        assert len(endpoint_clean) > 3 and "." in endpoint_clean, "Invalid agent endpoint format."
        assert len(capability_clean) >= 3, "Claimed capability description cannot be empty."
        assert stake_amount > 0, "Stake deposit amount must be greater than zero."

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
            last_probe_summary=f"Agent registered with capability '{capability_clean}' and {stake_amount} tokens staked. Awaiting behavioral probe audit."
        )

        self.agents[a_id] = new_agent
        return a_id

    @gl.public.write
    def audit_agent_capability(self, agent_id: str, challenger_address: str = "") -> None:
        assert agent_id in self.agents, "Agent record does not exist."

        agent = self.agents[agent_id]
        sender = str(gl.message.sender_address).lower()
        challenger_clean = challenger_address.strip().strip('"').strip("'").lower()
        if len(challenger_clean) == 0:
            challenger_clean = sender

        # Access Control Guardrail: Only agent, challenger, or contract owner can trigger probe audit
        assert sender == agent.agent_address or sender == challenger_clean or sender == self.owner, \
            "Only registered agent, challenger, or contract owner can trigger probe adjudication."

        assert agent.status in ("PROBATION", "ATTESTED_ACTIVE"), "Agent is not in an auditable status."
        assert int(agent.staked_deposit) > 0, "Agent has no staked deposit to slash or verify."

        # Derive probe URL from agent's registered endpoint using Google Public DNS health ping
        endpoint = agent.agent_endpoint
        capability = agent.claimed_capability

        probe_url = "https://dns.google/resolve?name=" + endpoint + "&type=TXT"

        def get_input() -> str:
            web_data = gl.nondet.web.render(probe_url, mode="text")
            return (
                f"Live Behavioral Probe API Response for Agent Endpoint '{endpoint}':\n\n"
                f"{web_data}\n\n"
                f"Claimed Agent Capability: '{capability}'"
            )

        task = (
            "You are an expert AI agent behavioral capability auditor for decentralized agent networks.\n"
            "Parse the live network probe API JSON response provided in the input.\n\n"
            "The JSON structure contains:\n"
            "- Status: DNS response status code (0 means successful resolution)\n"
            "- Answer: array of DNS records (or empty if offline/unreachable)\n\n"
            "Your job:\n"
            "1. Check if Status == 0 and Answer array exists with valid data.\n"
            "2. If endpoint is reachable and responsive, capability_passed is TRUE.\n"
            "3. If endpoint is unreachable, offline, or returns error status, capability_passed is FALSE.\n"
            "4. Calculate a performance quality score (0 to 100):\n"
            "   - Status == 0 and Answer present: score = 100\n"
            "   - Otherwise: score = 0\n\n"
            "Output JSON format:\n"
            "{\n"
            '  "endpoint_reachable": true/false,\n'
            '  "capability_passed": true/false,\n'
            '  "quality_score": <integer score 0 to 100>,\n'
            '  "summary": "<brief behavioral probe audit sentence>"\n'
            "}\n"
            "Respond ONLY with raw JSON."
        )

        criteria = (
            "Independently parse the network probe JSON response from the input. "
            "Inspect Status code and Answer array yourself. "
            "REJECT the leader's proposal if: "
            "(1) the proposed capability_passed boolean is inconsistent with (Status == 0 and Answer exists) in EITHER direction (true when offline/failing or false when online/passing), "
            "(2) the proposed quality_score does not match the calculated score in EITHER direction, or "
            "(3) the leader claims endpoint_reachable=false when valid response data is present. "
            "The output must be valid JSON with keys: endpoint_reachable, capability_passed, "
            "quality_score, and summary."
        )

        consensus_result = gl.eq_principle.prompt_non_comparative(
            get_input,
            task=task,
            criteria=criteria
        )

        # Clean thinking blocks and markdown wrappers
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

        assert reachable == True, "Live probe failed to reach target agent endpoint."

        staked_now = int(agent.staked_deposit)

        if passed and score_val >= 70:
            # Capability Probe Passed -> Attest Agent & Maintain Staked Deposit
            agent.status = "ATTESTED_ACTIVE"
            agent.quality_score = u256(score_val)
            agent.last_probe_summary = (
                f"BEHAVIORAL PROBE PASSED (Score: {score_val}/100): Agent endpoint '{endpoint}' verified operational. "
                f"Deposit of {staked_now} tokens maintained in active stake. " + summary
            )
        else:
            # Capability Probe Failed -> Slash Agent Deposit & Reward Challenger
            if int(self.total_staked_pool) >= staked_now:
                self.total_staked_pool = u256(int(self.total_staked_pool) - staked_now)

            agent.status = "SLASHED_FAILED"
            agent.quality_score = u256(score_val)
            agent.slashed_amount = u256(staked_now)
            agent.challenger_reward = u256(staked_now)
            agent.staked_deposit = u256(0)
            agent.last_probe_summary = (
                f"BEHAVIORAL PROBE FAILED (Score: {score_val}/100): Agent capability verification failed. "
                f"Full deposit of {staked_now} tokens slashed and allocated to challenger {challenger_clean}. " + summary
            )

        self.agents[agent_id] = agent

    @gl.public.write
    def withdraw_staked_deposit(self, agent_id: str) -> None:
        assert agent_id in self.agents, "Agent record does not exist."

        agent = self.agents[agent_id]
        sender = str(gl.message.sender_address).lower()

        # Access Control: Only the registered agent can withdraw their active stake
        assert sender == agent.agent_address, "Only the registered agent can withdraw active stake."
        assert agent.status == "ATTESTED_ACTIVE", "Stake can only be withdrawn if status is ATTESTED_ACTIVE."
        assert int(agent.staked_deposit) > 0, "No active staked deposit to withdraw."

        withdraw_val = int(agent.staked_deposit)
        if int(self.total_staked_pool) >= withdraw_val:
            self.total_staked_pool = u256(int(self.total_staked_pool) - withdraw_val)

        agent.staked_deposit = u256(0)
        agent.status = "WITHDRAWN"
        agent.last_probe_summary = f"Staked deposit of {withdraw_val} tokens successfully withdrawn by agent {sender}."

        self.agents[agent_id] = agent

    @gl.public.view
    def get_agent_vault(self, agent_id: str) -> AgentRecord:
        assert agent_id in self.agents, "Agent record does not exist."
        return self.agents[agent_id]

    @gl.public.view
    def is_agent_attested(self, agent_id: str) -> bool:
        assert agent_id in self.agents, "Agent record does not exist."
        return self.agents[agent_id].status == "ATTESTED_ACTIVE"

    @gl.public.view
    def get_staked_pool_balance(self) -> u256:
        return self.total_staked_pool

    @gl.public.view
    def get_total_agents(self) -> u256:
        return self.next_agent_id
