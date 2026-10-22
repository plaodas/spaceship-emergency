import unittest

from shipdiag.dialogue import append_reply


class DialogueTests(unittest.TestCase):
    def test_reply_is_appended_after_the_symptom(self):
        self.assertEqual(append_reply("右側が熱い。", "左舷は冷たい。"), "右側が熱い。左舷は冷たい。")
        self.assertEqual(append_reply("右側が熱い", "左舷は冷たい"), "右側が熱い。左舷は冷たい")

    def test_empty_reply_keeps_the_query(self):
        self.assertEqual(append_reply("右側が熱い。", "  "), "右側が熱い。")
        self.assertEqual(append_reply("", "左舷は冷たい"), "左舷は冷たい")


if __name__ == "__main__":
    unittest.main()
