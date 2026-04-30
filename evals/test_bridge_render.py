from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import flexo_syson_bridge  # noqa: E402


class BridgeRenderTests(unittest.TestCase):
    def test_fixture_renders_deterministic_sysml_subset(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "flexo-basic-package.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        rendered = flexo_syson_bridge.render_snapshot(snapshot)

        self.assertEqual(
            rendered,
            "\n".join(
                [
                    "// Generated from a Flexo SysML v2 REST export.",
                    "// Project: Fixture Project",
                    "// Commit: commit-1",
                    "",
                    "package Vehicle_Model {",
                    "  part def Transceiver {",
                    "    port rf_in;",
                    "    attribute gain_dB;",
                    "  }",
                    "  requirement def Link_Budget_Requirement;",
                    "}",
                    "",
                ]
            ),
        )

    def test_unsupported_elements_are_not_rendered(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "flexo-basic-package.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        rendered = flexo_syson_bridge.render_snapshot(snapshot)

        self.assertNotIn("OwningMembership", rendered)
        self.assertNotIn("NotRendered", rendered)


if __name__ == "__main__":
    unittest.main()
