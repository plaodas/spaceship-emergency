import copy
import unittest
from pathlib import Path

from shipdiag.fts import document_text, score_corpus
from shipdiag.gate import Q01
from shipdiag.prompt import render
from shipdiag.retrieve import assemble
from shipdiag.validate import load_corpus

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "FLT-017",
    "FLT-044",
    "FLT-028",
    "FLT-052",
    "FLT-061",
    "FLT-008",
    "CPL-03",
    "CPL-16",
    "CPL-18",
    "CPL-20",
}
CONCLUSION = "両方とも「直後だけ」になる"


class RetrieveTests(unittest.TestCase):
    def setUp(self):
        self.faults, self.couplings = load_corpus(ROOT / "data")
        self.seeds = [
            "FLT-017",
            "FLT-061",
            "FLT-044",
            "FLT-028",
            "FLT-052",
            "FLT-008",
        ]

    def test_coupling_is_absent_before_assembly_and_present_after(self):
        self.assertNotIn("CPL-03", self.seeds)
        cluster = assemble(self.faults, self.couplings, self.seeds)
        self.assertEqual({item["id"] for item in cluster}, EXPECTED)
        reasons = {item["id"]: item["reason"] for item in cluster}
        self.assertEqual(reasons["FLT-017"], "seed")
        self.assertEqual(reasons["CPL-03"], "coupling")
        self.assertNotIn("FLT-073", reasons)

    def test_dangling_downstream_is_dropped(self):
        faults = copy.deepcopy(self.faults)
        faults["FLT-028"]["derived"] = ["FLT-099"]
        faults["FLT-099"] = {
            "id": "FLT-099",
            "symptoms": "光子ノズルの流量が片側だけ増える。",
            "cause": "増量補正の下流でノズルが偏る。",
            "components": ["photon_nozzle"],
            "derived": [],
            "discriminators": ["推力が左右で揃わない。"],
        }
        cluster = assemble(faults, self.couplings, self.seeds)
        self.assertNotIn("FLT-099", {item["id"] for item in cluster})
        narrowed = assemble(faults, self.couplings, ["FLT-017", "FLT-028"])
        reasons = {item["id"]: item["reason"] for item in narrowed}
        self.assertEqual(reasons["FLT-044"], "path")
        self.assertNotIn("FLT-099", reasons)
        self.assertEqual(reasons["CPL-03"], "coupling")

    def test_cpl03_fts_score_is_zero(self):
        documents = [(card_id, document_text(card=card)) for card_id, card in self.faults.items()]
        documents.extend(
            (note_id, document_text(note=note)) for note_id, note in self.couplings.items()
        )
        scores = score_corpus(documents, Q01)
        self.assertEqual(scores["CPL-03"], 0)

    def test_prompt_lists_evidence_without_a_conclusion(self):
        cluster = assemble(self.faults, self.couplings, self.seeds)
        _system, user = render(Q01, cluster)
        for card_id in EXPECTED:
            self.assertIn(card_id, user)
        self.assertIn("右舷外板温度が左舷より高い。", user)
        self.assertNotIn(CONCLUSION, user)


if __name__ == "__main__":
    unittest.main()
