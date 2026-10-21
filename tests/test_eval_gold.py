import unittest
from pathlib import Path

import yaml

from shipdiag.validate import load_corpus

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IDS = [
    "Q01",
    "Q02",
    "Q03",
    "Q04",
    "Q05",
    "Q06",
    "Q07",
    "Q08",
    "Q10",
    "Q12",
    "Q15",
    "Q16",
    "Q17",
    "Q19",
    "Q20",
]


class EvalGoldTests(unittest.TestCase):
    def test_compose_gold_covers_fifteen_queries(self):
        gold = yaml.safe_load((ROOT / "data" / "eval" / "compose.yaml").read_text(encoding="utf-8"))
        faults, couplings = load_corpus(ROOT / "data")
        known = set(faults) | set(couplings)
        self.assertEqual([item["id"] for item in gold], EXPECTED_IDS)
        for item in gold:
            self.assertTrue(item["required"])
            self.assertLessEqual(set(item["required"]), known)
            self.assertLessEqual(set(item["avoid"]), known)
        q01 = gold[0]
        self.assertEqual(q01["required"], ["FLT-017", "FLT-044", "FLT-028", "CPL-03"])
        self.assertNotIn("FLT-028", gold[9]["required"])
        self.assertIn("FLT-028", gold[9]["avoid"])


if __name__ == "__main__":
    unittest.main()
