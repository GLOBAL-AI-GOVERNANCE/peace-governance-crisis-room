from __future__ import annotations

import copy
import hashlib
import json
import unittest


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def append_event(chain, event_type, data):
    event = {
        "sequence": len(chain) + 1,
        "event_type": event_type,
        "data": data,
        "previous_hash": "GENESIS" if not chain else chain[-1]["event_hash"],
    }
    event["event_hash"] = hashlib.sha256(canonical(event).encode()).hexdigest()
    chain.append(event)


def verify(chain):
    if not chain:
        return False
    previous = "GENESIS"
    for index, stored in enumerate(chain, start=1):
        if stored.get("sequence") != index or stored.get("previous_hash") != previous:
            return False
        event = dict(stored)
        claimed = event.pop("event_hash", "")
        actual = hashlib.sha256(canonical(event).encode()).hexdigest()
        if claimed != actual:
            return False
        previous = claimed
    return True


class AuditContractTests(unittest.TestCase):
    def test_chain_verifies(self):
        chain = []
        append_event(chain, "scenario_started", {"scenario_id": "s1"})
        append_event(chain, "decision_finalized", {"score": 100})
        self.assertTrue(verify(chain))

    def test_empty_chain_fails_closed(self):
        self.assertFalse(verify([]))

    def test_mutation_is_detected(self):
        chain = []
        append_event(chain, "scenario_started", {"scenario_id": "s1"})
        mutated = copy.deepcopy(chain)
        mutated[0]["data"]["scenario_id"] = "s2"
        self.assertFalse(verify(mutated))

    def test_tail_reordering_is_detected(self):
        chain = []
        append_event(chain, "a", {})
        append_event(chain, "b", {})
        chain.reverse()
        self.assertFalse(verify(chain))


if __name__ == "__main__":
    unittest.main()
