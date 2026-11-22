import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import vac_agent
import read_vac_nft
from vac_guard import VACGuard
from tools.make_status_json import build_status, EXPECTED_NAMES, MODULE_TOKENS


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


    def test_reader_rejects_wrong_chain_before_writing_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vac_genome.json"
            path.write_text("keep-existing-cache", encoding="utf-8")
            with (
                patch("sys.argv", ["read_vac_nft.py", "--chain", "ethereum", "--ids", "4-4", "--out", str(path)]),
                patch.object(read_vac_nft, "rpc", return_value="0x2105"),
            ):
                with self.assertRaises(SystemExit):
                    read_vac_nft.main()
            self.assertEqual(path.read_text(encoding="utf-8"), "keep-existing-cache")

    def test_reader_metadata_failure_does_not_overwrite_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vac_genome.json"
            path.write_text("keep-existing-cache", encoding="utf-8")
            with (
                patch("sys.argv", ["read_vac_nft.py", "--chain", "ethereum", "--ids", "4-4", "--out", str(path)]),
                patch.object(read_vac_nft, "rpc", side_effect=["0x1", "0x6000", "0x00", "0x00"]),
                patch.object(read_vac_nft, "standard", return_value="ERC-721"),
                patch.object(read_vac_nft, "decode_string", side_effect=["VAC Protocol", "VAC"]),
                patch.object(read_vac_nft, "token_uri", return_value="ipfs://unavailable"),
                patch.object(read_vac_nft, "fetch_json", side_effect=ConnectionError("IPFS unavailable")),
            ):
                with self.assertRaises(SystemExit):
                    read_vac_nft.main()
            self.assertEqual(path.read_text(encoding="utf-8"), "keep-existing-cache")


    def test_public_status_is_unavailable_when_any_module_metadata_fails(self):
        class FakeGuard:
            source_ok = True
            reason = "allowed: A02 held together with the constitution"
            def _metadata(self, token_id):
                if token_id == MODULE_TOKENS["006"]:
                    raise ConnectionError("gateway unavailable")
                key = next(k for k, v in MODULE_TOKENS.items() if v == token_id)
                return {"name": EXPECTED_NAMES[key], "description": "test"}
            def allowed(self):
                return True
            def params(self):
                return {"se_threshold": 3.0, "cooldown": 20, "zeta": 0.5}

        status = build_status(FakeGuard())
        self.assertEqual(status["status"], "UNAVAILABLE")
        self.assertIsNone(status["modules"])
        self.assertIsNone(status["rules"])
        self.assertIn("006", status["module_errors"])

    def test_public_status_distinguishes_creator_veto_from_rpc_failure(self):
        class FakeGuard:
            source_ok = True
            reason = "halted: creator veto (A02 has been transferred out)"
            def _metadata(self, token_id):
                key = next(k for k, v in MODULE_TOKENS.items() if v == token_id)
                return {"name": EXPECTED_NAMES[key], "description": "test"}
            def allowed(self):
                return False
            def params(self):
                raise AssertionError("params must not be read while halted")

        status = build_status(FakeGuard())
        self.assertEqual(status["status"], "HALTED")
        self.assertIsNone(status["modules"])
        self.assertIsNone(status["rules"])

        FakeGuard.reason = "cannot read the chain (ConnectionError) → halt (fail-closed)"
        unavailable = build_status(FakeGuard())
        self.assertEqual(unavailable["status"], "UNAVAILABLE")

    def test_public_status_runs_only_with_all_expected_modules(self):
        class FakeGuard:
            source_ok = True
            reason = "allowed: A02 held together with the constitution"
            def _metadata(self, token_id):
                key = next(k for k, v in MODULE_TOKENS.items() if v == token_id)
                return {"name": EXPECTED_NAMES[key], "description": "test"}
            def allowed(self):
                return True
            def params(self):
                return {"se_threshold": 3.0, "cooldown": 20, "zeta": 0.5}

        status = build_status(FakeGuard())
        self.assertEqual(status["status"], "RUNNING")
        self.assertEqual(set(status["modules"]), set(MODULE_TOKENS))
        self.assertEqual(status["rules"]["zeta"], 0.5)

    def test_params_cannot_bypass_creator_veto_even_when_cached(self):
        guard = VACGuard.__new__(VACGuard)
        guard.allowed = lambda: False
        guard.reason = "creator veto"
        guard._params = {"se_threshold": 3.0, "cooldown": 20, "zeta": 0.5}
        with self.assertRaises(PermissionError):
            guard.params()


if __name__ == "__main__":
    unittest.main()
