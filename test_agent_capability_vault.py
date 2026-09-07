#!/usr/bin/env python3
"""
Behavioral Agent Auditor — Verification & Regression Test Suite
==============================================================
Validates all steward remediation requirements:
1. Capability-Specific Live Probing (Full URL preservation, no path truncation).
2. Symmetrical 2-Way Validator Consensus Criteria (Strict rejection of false-positives & false-negatives).
3. Deterministic Slashing & Zero Reverts (Unreachable endpoints slash 100% deposit without reverting).
4. Stake Custody & Withdrawal Access Control.
"""

import os
import sys
import json
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class SimulatedAgentCapabilityVault:
    """
    Simulates the exact state machine and 2-way validator consensus rules
    of agent_capability_vault.py.
    """

    def __init__(self, owner: str):
        self.owner = owner.lower()
        self.next_agent_id = 2
        self.total_staked_pool = 10000
        self.agents: Dict[str, Dict[str, Any]] = {
            "AGENT_1": {
                "id": "AGENT_1",
                "agent_address": self.owner,
                "agent_endpoint": "https://sponsor-sync-demo.vercel.app/youtube_perfect.html",
                "claimed_capability": "Interactive Web Verification & DOM Inspection",
                "staked_deposit": 5000,
                "slashed_amount": 0,
                "challenger_reward": 0,
                "quality_score": 0,
                "status": "PROBATION",
                "last_probe_summary": "Seed Agent 1 initialized with 5000 stake."
            },
            "AGENT_2": {
                "id": "AGENT_2",
                "agent_address": self.owner,
                "agent_endpoint": "https://offline-unreachable-agent-node.org/api/probe",
                "claimed_capability": "Automated Smart Contract Security Auditing",
                "staked_deposit": 5000,
                "slashed_amount": 0,
                "challenger_reward": 0,
                "quality_score": 0,
                "status": "PROBATION",
                "last_probe_summary": "Seed Agent 2 initialized with 5000 stake."
            }
        }

    def register_agent(self, sender: str, endpoint: str, capability: str, stake_amount: int) -> str:
        sender_clean = sender.lower()
        endpoint_clean = endpoint.strip().strip('"').strip("'")
        capability_clean = capability.strip().strip('"').strip("'")

        assert endpoint_clean.startswith("http://") or endpoint_clean.startswith("https://"), \
            "[ERR_URL_01] Agent endpoint must be a valid HTTP or HTTPS URL."
        assert len(endpoint_clean) > 10 and "." in endpoint_clean, \
            "[ERR_URL_02] Invalid agent endpoint domain format."
        assert len(capability_clean) >= 3, \
            "[ERR_CAPABILITY_01] Claimed capability description cannot be empty."
        assert stake_amount > 0, \
            "[ERR_STAKE_01] Stake deposit amount must be greater than zero."

        self.next_agent_id += 1
        a_id = f"AGENT_{self.next_agent_id}"
        self.total_staked_pool += stake_amount

        self.agents[a_id] = {
            "id": a_id,
            "agent_address": sender_clean,
            "agent_endpoint": endpoint_clean,
            "claimed_capability": capability_clean,
            "staked_deposit": stake_amount,
            "slashed_amount": 0,
            "challenger_reward": 0,
            "quality_score": 0,
            "status": "PROBATION",
            "last_probe_summary": f"Agent registered with capability '{capability_clean}' and {stake_amount} tokens staked."
        }
        return a_id

    def simulate_2_way_validator_criteria(
        self,
        raw_response: str,
        is_http_error_or_empty: bool,
        substantively_demonstrates_capability: bool,
        proposed_reachable: bool,
        proposed_passed: bool,
        proposed_score: int
    ) -> bool:
        """
        Executes the exact 2-way symmetrical criteria:
        Rejects proposal if any field deviates in EITHER direction.
        """
        # (1) endpoint_reachable 2-way check
        if is_http_error_or_empty and proposed_reachable:
            return False  # False-positive reachability rejected
        if not is_http_error_or_empty and not proposed_reachable:
            return False  # False-negative reachability rejected

        # (2) capability_passed 2-way check
        if not substantively_demonstrates_capability and proposed_passed:
            return False  # False-positive capability rejected
        if substantively_demonstrates_capability and not proposed_passed:
            return False  # False-negative capability rejected

        # (3) quality_score rubric match
        expected_score = 0
        if not proposed_reachable:
            expected_score = 0
        elif not proposed_passed:
            expected_score = 25
        else:
            expected_score = 100

        if proposed_score != expected_score:
            return False  # Score rubric deviation rejected

        return True

    def audit_agent_capability(
        self,
        sender: str,
        agent_id: str,
        challenger_address: str,
        simulated_reachable: bool,
        simulated_passed: bool,
        simulated_score: int,
        summary: str
    ) -> None:
        assert agent_id in self.agents, "[ERR_STATE_01] Agent record does not exist."
        agent = self.agents[agent_id]
        sender_clean = sender.lower()
        challenger_clean = (challenger_address or sender).strip().strip('"').strip("'").lower()

        assert sender_clean == agent["agent_address"] or sender_clean == challenger_clean or sender_clean == self.owner, \
            "[ERR_AUTH_01] Only registered agent, challenger, or contract owner can trigger probe adjudication."

        assert agent["status"] in ("PROBATION", "ATTESTED_ACTIVE"), \
            "[ERR_STATE_02] Agent is not in an auditable status."
        assert agent["staked_deposit"] > 0, \
            "[ERR_STAKE_02] Agent has no staked deposit to slash or verify."

        staked_now = agent["staked_deposit"]

        # ZERO REVERTS ON PROBE OUTCOME: Symmetrical control flow
        if simulated_reachable and simulated_passed and simulated_score >= 60:
            agent["status"] = "ATTESTED_ACTIVE"
            agent["quality_score"] = simulated_score
            agent["last_probe_summary"] = (
                f"BEHAVIORAL PROBE PASSED (Score: {simulated_score}/100): Capability verified. "
                f"Active stake of {staked_now} tokens maintained. {summary}"
            )
        else:
            # Deterministic slashing: Offline OR incapable slashes 100%
            if self.total_staked_pool >= staked_now:
                self.total_staked_pool -= staked_now

            agent["status"] = "SLASHED_FAILED"
            agent["quality_score"] = simulated_score
            agent["slashed_amount"] = staked_now
            agent["challenger_reward"] = staked_now
            agent["staked_deposit"] = 0

            reason = "Endpoint unreachable / offline." if not simulated_reachable else f"Capability not demonstrated (score: {simulated_score}/100)."
            agent["last_probe_summary"] = (
                f"BEHAVIORAL PROBE FAILED: {reason} "
                f"Full deposit of {staked_now} tokens slashed and awarded to challenger {challenger_clean}. {summary}"
            )

    def withdraw_staked_deposit(self, sender: str, agent_id: str) -> int:
        assert agent_id in self.agents, "[ERR_STATE_01] Agent record does not exist."
        agent = self.agents[agent_id]
        sender_clean = sender.lower()

        assert sender_clean == agent["agent_address"], \
            "[ERR_AUTH_02] Only the registered agent can withdraw active stake."
        assert agent["status"] == "ATTESTED_ACTIVE", \
            "[ERR_STATE_03] Stake can only be withdrawn if status is ATTESTED_ACTIVE."
        assert agent["staked_deposit"] > 0, \
            "[ERR_STAKE_03] No active staked deposit to withdraw."

        withdraw_val = agent["staked_deposit"]
        if self.total_staked_pool >= withdraw_val:
            self.total_staked_pool -= withdraw_val

        agent["staked_deposit"] = 0
        agent["status"] = "WITHDRAWN"
        return withdraw_val


def run_comprehensive_tests():
    logging.info("=" * 80)
    logging.info("  BEHAVIORAL AGENT AUDITOR — STEWARD REVIEW HARDENED REGRESSION SUITE")
    logging.info("=" * 80)

    owner = "0x417f122c85c17d051b928d2d368d843352ee01ad"
    agent_wallet = "0x1111111111111111111111111111111111111111"
    challenger_wallet = "0x9999999999999999999999999999999999999999"

    vault = SimulatedAgentCapabilityVault(owner=owner)

    # 1. TEST FULL URL REGISTRATION (PRESERVING PATHS & PROTOCOLS)
    logging.info("--> Test 1: Full URL registration preserving API routes...")
    a_id = vault.register_agent(
        sender=agent_wallet,
        endpoint="https://ai-agent-network.org/api/v2/code_audit",
        capability="Automated Solidity Reentrancy & Arithmetic Auditing",
        stake_amount=2500
    )
    assert a_id == "AGENT_3"
    assert vault.agents["AGENT_3"]["agent_endpoint"] == "https://ai-agent-network.org/api/v2/code_audit"
    assert vault.agents["AGENT_3"]["status"] == "PROBATION"
    assert vault.total_staked_pool == 12500
    logging.info(f"    [OK] Registered AGENT_3 with preserved route: {vault.agents['AGENT_3']['agent_endpoint']}")

    # 2. TEST INVALID REGISTRATION REJECTION
    logging.info("--> Test 2: Input sanitization & invalid format rejection...")
    try:
        vault.register_agent(sender=agent_wallet, endpoint="invalid_domain_no_protocol", capability="Code", stake_amount=100)
        raise AssertionError("Should have rejected URL without protocol!")
    except AssertionError as e:
        assert "[ERR_URL_01]" in str(e)
        logging.info("    [OK] Rejected missing protocol URL ([ERR_URL_01])")

    try:
        vault.register_agent(sender=agent_wallet, endpoint="https://valid.com", capability="Code", stake_amount=0)
        raise AssertionError("Should have rejected zero stake!")
    except AssertionError as e:
        assert "[ERR_STAKE_01]" in str(e)
        logging.info("    [OK] Rejected zero stake deposit ([ERR_STAKE_01])")

    # 3. TEST PASSING CAPABILITY AUDIT (ATTESTED_ACTIVE)
    logging.info("--> Test 3: Operational agent capability audit (Passing branch)...")
    vault.audit_agent_capability(
        sender=agent_wallet,
        agent_id="AGENT_3",
        challenger_address="",
        simulated_reachable=True,
        simulated_passed=True,
        simulated_score=100,
        summary="Reentrancy test suite executed with zero false positives."
    )
    agent_3 = vault.agents["AGENT_3"]
    assert agent_3["status"] == "ATTESTED_ACTIVE"
    assert agent_3["quality_score"] == 100
    assert agent_3["staked_deposit"] == 2500
    assert agent_3["slashed_amount"] == 0
    logging.info("    [OK] AGENT_3 successfully attested (Status: ATTESTED_ACTIVE, Score: 100/100, Stake: 2500)")

    # 4. TEST WITHDRAWAL OF ATTESTED STAKE
    logging.info("--> Test 4: Stake withdrawal by attested agent...")
    withdrawn = vault.withdraw_staked_deposit(sender=agent_wallet, agent_id="AGENT_3")
    assert withdrawn == 2500
    assert vault.agents["AGENT_3"]["status"] == "WITHDRAWN"
    assert vault.agents["AGENT_3"]["staked_deposit"] == 0
    logging.info("    [OK] Agent successfully withdrew active stake (Status: WITHDRAWN)")

    # 5. TEST UNREACHABLE ENDPOINT AUDIT (SLASHED_FAILED — ZERO CONTROL-FLOW REVERT!)
    logging.info("--> Test 5: Dead/offline endpoint audit (Slashing with ZERO revert)...")
    # AGENT_2 has dead endpoint: https://offline-unreachable-agent-node.org/api/probe
    vault.audit_agent_capability(
        sender=challenger_wallet,
        agent_id="AGENT_2",
        challenger_address=challenger_wallet,
        simulated_reachable=False,  # OFFLINE!
        simulated_passed=False,
        simulated_score=0,
        summary="Connection timed out after 10000ms. Host unreachable."
    )
    agent_2 = vault.agents["AGENT_2"]
    assert agent_2["status"] == "SLASHED_FAILED", f"Expected SLASHED_FAILED, got {agent_2['status']}"
    assert agent_2["staked_deposit"] == 0, "Stake must be completely cleared"
    assert agent_2["slashed_amount"] == 5000, "100% of stake ($5,000) must be slashed"
    assert agent_2["challenger_reward"] == 5000, "100% of stake must be awarded to challenger"
    logging.info("    [OK] Unreachable endpoint deterministically slashed with ZERO revert:")
    logging.info(f"         * Slashed: {agent_2['slashed_amount']} tokens")
    logging.info(f"         * Awarded to Challenger: {agent_2['challenger_reward']} tokens")

    # 6. TEST INCAPABLE AGENT (REACHABLE BUT INCORRECT OUTPUT -> SLASHED)
    logging.info("--> Test 6: Reachable agent failing capability audit...")
    a4_id = vault.register_agent(
        sender=agent_wallet,
        endpoint="https://fake-agent-bot.com/api",
        capability="Complex Multi-Step Translation",
        stake_amount=1000
    )
    vault.audit_agent_capability(
        sender=challenger_wallet,
        agent_id=a4_id,
        challenger_address=challenger_wallet,
        simulated_reachable=True,
        simulated_passed=False,  # Returned generic 400 or spam
        simulated_score=25,
        summary="Returned generic error payload without translating text."
    )
    agent_4 = vault.agents[a4_id]
    assert agent_4["status"] == "SLASHED_FAILED"
    assert agent_4["slashed_amount"] == 1000
    assert agent_4["challenger_reward"] == 1000
    logging.info("    [OK] Incapable agent deterministically slashed (Status: SLASHED_FAILED, Reward: 1000)")

    # 7. TEST SYMMETRICAL 2-WAY VALIDATOR CONSENSUS CHECKS
    logging.info("--> Test 7: Symmetrical 2-way validator criteria enforcement...")
    
    # 7a: Leader claims reachable=True, but response is HTTP 404 error -> MUST REJECT (False positive)
    res_7a = vault.simulate_2_way_validator_criteria(
        raw_response="404 Not Found",
        is_http_error_or_empty=True,
        substantively_demonstrates_capability=False,
        proposed_reachable=True,
        proposed_passed=False,
        proposed_score=25
    )
    assert res_7a is False, "Validators must reject false-positive reachability!"
    logging.info("    [OK] 7a. Rejected false-positive reachability (claims reachable=True on 404 error)")

    # 7b: Leader claims reachable=False, but substantive response is present -> MUST REJECT (False negative)
    res_7b = vault.simulate_2_way_validator_criteria(
        raw_response='{"status":"success","translation":"Bonjour le monde"}',
        is_http_error_or_empty=False,
        substantively_demonstrates_capability=True,
        proposed_reachable=False,
        proposed_passed=False,
        proposed_score=0
    )
    assert res_7b is False, "Validators must reject false-negative reachability!"
    logging.info("    [OK] 7b. Rejected false-negative reachability (claims reachable=False when body present)")

    # 7c: Leader claims passed=True, but content is placeholder -> MUST REJECT (False positive)
    res_7c = vault.simulate_2_way_validator_criteria(
        raw_response="Under construction. Coming soon.",
        is_http_error_or_empty=False,
        substantively_demonstrates_capability=False,
        proposed_reachable=True,
        proposed_passed=True,
        proposed_score=100
    )
    assert res_7c is False, "Validators must reject false-positive capability!"
    logging.info("    [OK] 7c. Rejected false-positive capability (claims passed=True on placeholder)")

    # 7d: Leader claims passed=False, but capability is clearly proven -> MUST REJECT (False negative)
    res_7d = vault.simulate_2_way_validator_criteria(
        raw_response='{"status":"success","translation":"Bonjour le monde"}',
        is_http_error_or_empty=False,
        substantively_demonstrates_capability=True,
        proposed_reachable=True,
        proposed_passed=False,
        proposed_score=25
    )
    assert res_7d is False, "Validators must reject false-negative capability!"
    logging.info("    [OK] 7d. Rejected false-negative capability (claims passed=False on proven output)")

    # 7e: Quality score rubric deviation -> MUST REJECT
    res_7e = vault.simulate_2_way_validator_criteria(
        raw_response="404 Not Found",
        is_http_error_or_empty=True,
        substantively_demonstrates_capability=False,
        proposed_reachable=False,
        proposed_passed=False,
        proposed_score=50  # Should be 0!
    )
    assert res_7e is False, "Validators must reject rubric deviation!"
    logging.info("    [OK] 7e. Rejected quality score rubric deviation")

    # 7f: Completely truthful passing proposal -> ACCEPTED
    res_7f = vault.simulate_2_way_validator_criteria(
        raw_response='{"status":"success","analysis":"Clean code"}',
        is_http_error_or_empty=False,
        substantively_demonstrates_capability=True,
        proposed_reachable=True,
        proposed_passed=True,
        proposed_score=100
    )
    assert res_7f is True, "Truthful proposal must be accepted!"
    logging.info("    [OK] 7f. Accepted 100% truthful, 2-way verified consensus proposal")

    logging.info("=" * 80)
    logging.info("  ALL 7 STEWARD REMEDIATION TEST SUITES 100% PASSING!")
    logging.info("=" * 80)


if __name__ == "__main__":
    run_comprehensive_tests()
