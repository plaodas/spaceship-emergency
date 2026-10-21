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
        for doc_id, quotes in self.quotes.items():
            if doc_id in self.faults:
                self.assertEqual(self.faults[doc_id]["symptoms"], quotes[0])
            else:
                self.assertEqual(self.couplings[doc_id]["text"], quotes[0])
        for fault_id in EVIDENCE_IDS:
            self.assertEqual(self.faults[fault_id]["cause"], self.quotes[fault_id][1])

    def test_crew_word_is_rejected(self):
        faults = copy.deepcopy(self.faults)
        faults["FLT-017"]["symptoms"] = "燃費が読み取れる。" + ("計器を確認する。" * 8)
        issues = validate_corpus(faults, self.couplings, complete=False)
        self.assertTrue(any("乗員語「燃費」" in issue for issue in issues))

    def test_missing_derived_target_is_rejected(self):
        faults = copy.deepcopy(self.faults)
        faults["FLT-017"]["derived"] = ["FLT-999"]
        issues = validate_corpus(faults, self.couplings, complete=False)
        self.assertTrue(any("FLT-999" in issue for issue in issues))

    def test_four_facts_in_one_document_are_rejected(self):
        faults = copy.deepcopy(self.faults)
        faults["FLT-028"]["symptoms"] = (
            "超光速の航法を終えて通常空間へ戻ったあと、右舷外板の温度が上がる。"
            "反物質の使用量が増加する。同一弁体で合流している。"
            "計器は両経路の熱の行き場を同時に示す。"
        )
        issues = validate_corpus(faults, self.couplings, complete=False)
        self.assertTrue(any("同一本文" in issue for issue in issues))

    def test_complete_corpus_is_closed(self):
        self.assertEqual(len(self.faults), 100)
        self.assertEqual(len(self.couplings), 24)
        self.assertEqual(validate_corpus(self.faults, self.couplings, complete=True), [])
        self.assertEqual(self.faults["FLT-028"]["derived"], ["FLT-073"])
        self.assertEqual(self.faults["FLT-073"]["role"], "local")


if __name__ == "__main__":
    unittest.main()
