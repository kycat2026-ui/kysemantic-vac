import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import vac_agent
from vac_guard import VACGuard


def valid_genome():
    return {
        "contract": "0x4e22b334e53c1dc7e266b5996d32c05a6ac8f4fb",
        "chain": "ethereum",
        "standard": "ERC-721",
        "name": "VAC Protocol",
        "tokens": {
            "4": {"tokenURI": "ipfs://axiom", "metadata": {"name": "VAC Axiom #003"}},
            "13": {"tokenURI": "ipfs://a02", "metadata": {"name": "VAC Amendment II: Creator Veto"}},
        },
    }


class FailClosedTests(unittest.TestCase):
    def test_missing_a02_halts(self):
        halted, reason = vac_agent.creator_veto({}, {"003": {"token_id": 4}})
        self.assertTrue(halted)
        self.assertIn("A02", reason)

    def test_missing_axiom_003_halts(self):
        halted, reason = vac_agent.creator_veto({"A02": {"token_id": 13}}, {})
        self.assertTrue(halted)
        self.assertIn("#003", reason)

    def test_online_read_failure_never_uses_stale_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vac_genome.json"
            path.write_text(json.dumps(valid_genome()), encoding="utf-8")
            with patch.object(vac_agent.subprocess, "run", return_value=SimpleNamespace(returncode=1)):
                with self.assertRaises(SystemExit):
                    vac_agent.load_genome(str(path), offline=False)

    def test_valid_offline_genome_is_accepted_for_explicit_offline_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vac_genome.json"
            path.write_text(json.dumps(valid_genome()), encoding="utf-8")
            genome = vac_agent.load_genome(str(path), offline=True)
            self.assertEqual(genome["name"], "VAC Protocol")

    def test_wrong_chain_genome_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vac_genome.json"
            data = valid_genome()
            data["chain"] = "base"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(SystemExit):
                vac_agent.load_genome(str(path), offline=True)

    def test_missing_constitution_token_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vac_genome.json"
            data = valid_genome()
            del data["tokens"]["4"]
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(SystemExit):
                vac_agent.load_genome(str(path), offline=True)

    def test_params_cannot_bypass_creator_veto_even_when_cached(self):
        guard = VACGuard.__new__(VACGuard)
        guard.allowed = lambda: False
        guard.reason = "creator veto"
        guard._params = {"se_threshold": 3.0, "cooldown": 20, "zeta": 0.5}
        with self.assertRaises(PermissionError):
            guard.params()


if __name__ == "__main__":
    unittest.main()
