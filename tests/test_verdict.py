import unittest

from shipdiag.verdict import parse_verdict, verdict_issues

Q01 = """右舷の残熱と弁の固着と増量補正を、同じ弁で結びます。
cited: FLT-017 FLT-044 FLT-028 CPL-03
primary: FLT-017 FLT-044 FLT-028
rejected: FLT-052 FLT-061 FLT-008
measurements: 左舷外板は同じ時間窓では上がらない
"""

Q12 = """復帰後の外板温度だけを採ります。
cited: FLT-017 FLT-048 CPL-01
primary: FLT-017 FLT-048
rejected: FLT-028
measurements: 反物質の使用量は増えていない
"""


class VerdictTests(unittest.TestCase):
    def test_q01_cites_required_and_does_not_promote_avoid(self):
        verdict = parse_verdict(Q01)
        required = ["FLT-017", "FLT-044", "FLT-028", "CPL-03"]
        avoid = ["FLT-052", "FLT-061", "FLT-008"]
        self.assertEqual(verdict_issues(verdict, required, avoid), [])
        self.assertEqual(verdict["measurements"], ["左舷外板は同じ時間窓では上がらない"])

    def test_avoid_in_the_cluster_is_not_an_issue_until_it_is_primary(self):
        verdict = parse_verdict(Q01)
        verdict["cited"].append("FLT-052")
        self.assertEqual(verdict_issues(verdict, ["FLT-017", "FLT-044", "FLT-028", "CPL-03"], ["FLT-052"]), [])
        verdict["primary"].append("FLT-052")
        self.assertIn("FLT-052", verdict_issues(verdict, ["FLT-017"], ["FLT-052"])[0])

    def test_q12_may_cite_flt028_but_not_as_primary(self):
        self.assertEqual(
            verdict_issues(parse_verdict(Q12), ["FLT-017", "FLT-048", "CPL-01"], ["FLT-028"]),
            [],
        )
        promoted = Q12.replace("primary: FLT-017 FLT-048", "primary: FLT-017 FLT-028")
        issues = verdict_issues(parse_verdict(promoted), ["FLT-017", "FLT-048", "CPL-01"], ["FLT-028"])
        self.assertTrue(any("FLT-028" in issue for issue in issues))

    def test_commas_between_ids_are_ignored(self):
        text = Q01.replace(
            "cited: FLT-017 FLT-044 FLT-028 CPL-03",
            "cited: FLT-017, FLT-044, FLT-028, CPL-03",
        )
        verdict = parse_verdict(text)
        self.assertEqual(verdict["cited"], ["FLT-017", "FLT-044", "FLT-028", "CPL-03"])

    def test_block_before_prose_still_parses(self):
        text = "cited: FLT-017\nprimary: FLT-017\nrejected: FLT-052\nmeasurements: 左舷は上がらない\n\nそのあと説明を続ける。"
        verdict = parse_verdict(text)
        self.assertEqual(verdict["cited"], ["FLT-017"])
        self.assertEqual(verdict["rejected"], ["FLT-052"])

    def test_missing_block_fails(self):
        self.assertIsNone(parse_verdict("右舷が熱いので弁を見ます。"))
        self.assertEqual(verdict_issues(None, ["FLT-017"], []), ["採点行がありません"])


if __name__ == "__main__":
    unittest.main()
