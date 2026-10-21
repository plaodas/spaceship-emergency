import unittest
from pathlib import Path

import chromadb

from shipdiag.documents import fault_embed_text, fault_metadata
from shipdiag.gate import Q01
from shipdiag.index import index_faults, search
from shipdiag.validate import load_corpus

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.faults, self.couplings = load_corpus(DATA)
        self.client = chromadb.EphemeralClient()

    def test_embed_text_includes_card_fields_and_component_name(self):
        card = self.faults["FLT-017"]
        text = fault_embed_text(card)
        self.assertIn(card["name"], text)
        self.assertIn(card["symptoms"], text)
        self.assertIn(card["cause"], text)
        self.assertIn("右舷折畳みコイル", text)

    def test_metadata_joins_lists(self):
        meta = fault_metadata(self.faults["FLT-017"])
        self.assertEqual(meta["components"], "starboard_fold_coil")
        self.assertEqual(meta["triggers"], "after_jump")
        self.assertEqual(meta["derived"], "FLT-044")
        self.assertEqual(meta["severity"], 2)

    def test_matching_query_ranks_flt017_first(self):
        target = fault_embed_text(self.faults["FLT-017"])

        def embed(texts):
            return [[1.0, 0.0] if text in (target, Q01) else [0.0, 1.0] for text in texts]

        collection = index_faults(self.faults, embed, self.client, "stub")
        hits = search(collection, embed([Q01])[0], k=len(self.faults))
        self.assertEqual(hits[0][0], "FLT-017")

    def test_collection_has_faults_only(self):
        def embed(texts):
            return [[float(i), 1.0] for i, _text in enumerate(texts)]

        collection = index_faults(self.faults, embed, self.client, "stub")
        ids = set(collection.get()["ids"])
        self.assertEqual(ids, set(self.faults))
        self.assertEqual(len(ids), 6)
        self.assertNotIn("CPL-03", ids)
        self.assertIn("CPL-03", self.couplings)


if __name__ == "__main__":
    unittest.main()
