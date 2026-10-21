import copy
import re
import unittest
from pathlib import Path

from shipdiag.validate import load_corpus, validate_corpus

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DEMO = (ROOT / "docs" / "05-demo-diagnosis.md").read_text(encoding="utf-8")
EVIDENCE_IDS = ("FLT-017", "FLT-044", "FLT-028")


def _quotes_by_id(text):
    found = {}
    for section in re.split(r"^### ", text, flags=re.M)[1:]:
        title = section.split("\n", 1)[0]
        match = re.match(r"(FLT-\d+|CPL-\d+)", title)
        if match is None:
            continue
        found[match.group(1)] = re.findall(r"^> (.+)$", section, re.M)
    return found


class ValidateDemoTests(unittest.TestCase):
    def setUp(self):
        self.faults, self.couplings = load_corpus(DATA)
        self.quotes = _quotes_by_id(DEMO)

    def test_demo_passes_while_incomplete(self):
        self.assertEqual(validate_corpus(self.faults, self.couplings, complete=False), [])

    def test_flt044_trigger_is_only_after_heat_pulse(self):
        self.assertEqual(self.faults["FLT-044"]["triggers"], ["after_heat_pulse"])

    def test_reserved_prose_matches_demo_doc(self):
        for fault_id, card in self.faults.items():
            self.assertEqual(card["symptoms"], self.quotes[fault_id][0])
        for fault_id in EVIDENCE_IDS:
            self.assertEqual(self.faults[fault_id]["cause"], self.quotes[fault_id][1])
        self.assertEqual(self.couplings["CPL-03"]["text"], self.quotes["CPL-03"][0])

    def test_crew_word_is_rejected(self):
        faults = copy.deepcopy(self.faults)
        faults["FLT-017"]["symptoms"] = "燃費が読み取れる。" + ("計器を確認する。" * 8)
        issues = validate_corpus(faults, self.couplings, complete=False)
        self.assertTrue(any("乗員語「燃費」" in issue for issue in issues))

    def test_missing_derived_target_is_rejected(self):
        faults = copy.deepcopy(self.faults)
        faults["FLT-017"]["derived"] = ["FLT-099"]
        issues = validate_corpus(faults, self.couplings, complete=False)
        self.assertTrue(any("FLT-099" in issue for issue in issues))

    def test_four_facts_in_one_document_are_rejected(self):
        faults = copy.deepcopy(self.faults)
        faults["FLT-028"]["symptoms"] = (
            "超光速の航法を終えて通常空間へ戻ったあと、右舷外板の温度が上がる。"
            "反物質の使用量が増加する。同一弁体で合流している。"
            "計器は両経路の熱の行き場を同時に示す。"
        )
        issues = validate_corpus(faults, self.couplings, complete=False)
        self.assertTrue(any("同一本文" in issue for issue in issues))

    def test_complete_mode_rejects_the_demo_set(self):
        issues = validate_corpus(self.faults, self.couplings, complete=True)
        self.assertTrue(any("FLT-028" in issue and "derived" in issue for issue in issues))
        self.assertTrue(any("配分" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
