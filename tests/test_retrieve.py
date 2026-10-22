import copy
import unittest
from pathlib import Path

from shipdiag.fts import document_text, score_corpus
from shipdiag.gate import Q01
from shipdiag.prompt import render
from shipdiag.eval_compose import load_gold
from shipdiag.retrieve import assemble, seeds_for, split_clauses
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
        self.assertEqual(cluster["mode"], "compose")
        self.assertEqual({item["id"] for item in cluster["items"]}, EXPECTED)
        reasons = {item["id"]: item["reason"] for item in cluster["items"]}
        self.assertEqual(reasons["FLT-017"], "seed")
        self.assertEqual(reasons["CPL-03"], "coupling")
        self.assertNotIn("CPL-16", reasons)
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
        self.assertNotIn("FLT-099", {item["id"] for item in cluster["items"]})
        narrowed = assemble(faults, self.couplings, ["FLT-017", "FLT-028"])
        reasons = {item["id"]: item["reason"] for item in narrowed["items"]}
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
        system, user = render(Q01, cluster["items"], cluster["mode"])
        for card_id in EXPECTED:
            self.assertIn(card_id, user)
        self.assertIn("右舷外板温度が左舷より高い。", user)
        self.assertNotIn(CONCLUSION, user)
        self.assertIn("cited:", system)
        self.assertIn("結合ノートを1枚以上", system)

    def test_other_modes_do_not_require_a_coupling(self):
        for mode in ("independent", "single"):
            system, _user = render("熱くはない。", [], mode)
            self.assertNotIn("結合ノートを1枚以上", system)
            self.assertIn("measurements:", system)

    def test_unconnected_seeds_are_independent(self):
        cluster = assemble(self.faults, self.couplings, ["FLT-061", "FLT-008"])
        self.assertEqual(cluster["mode"], "independent")
        self.assertFalse(any(item["reason"] == "coupling" for item in cluster["items"]))

    def test_one_seed_without_a_coupling_is_single(self):
        cluster = assemble(self.faults, self.couplings, ["FLT-061"])
        self.assertEqual(cluster["mode"], "single")
        self.assertEqual([item["id"] for item in cluster["items"]], ["FLT-061"])

    def test_clauses_merge_by_nearer_distance(self):
        self.assertEqual(split_clauses("熱い。燃費。"), ["熱い", "燃費"])
        self.assertEqual(split_clauses("熱い。"), ["熱い"])

        def embed(texts):
            if texts == ["熱い。"]:
                return [[9.0]]
            return [[float(index)] for index, _text in enumerate(texts)]

        def search_one(vector):
            if vector == [9.0]:
                return [("FLT-017", 0.2)]
            if vector[0] == 0.0:
                return [("FLT-017", 0.4), ("FLT-028", 0.2)]
            return [("FLT-017", 0.1), ("FLT-044", 0.3)]

        single = seeds_for("熱い。", embed, search_one)
        self.assertEqual(single, [("FLT-017", 0.2)])
        merged = seeds_for("熱い。燃費。", embed, search_one, limit=2)
        self.assertEqual([item[0] for item in merged], ["FLT-017", "FLT-028"])

    def test_required_couplings_have_zero_fts_score(self):
        documents = [(note_id, document_text(note=note)) for note_id, note in self.couplings.items()]
        overlaps = []
        for item in load_gold():
            scores = score_corpus(documents, item["query"])
            for doc_id in item["required"]:
                if doc_id.startswith("CPL") and scores[doc_id] != 0:
                    overlaps.append(f"{item['id']} {doc_id}")
        self.assertEqual(overlaps, [])


if __name__ == "__main__":
    unittest.main()
