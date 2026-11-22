"""Headless test of the Streamlit interface (runs only where streamlit is installed)."""
import importlib.util
import json
import unittest

from helpers import ROOT

HAS_STREAMLIT = importlib.util.find_spec("streamlit") is not None
EXAMPLE = "Example 1 — analyst coverage (Table 3)"
EXAMPLE_2 = "Example 2 — board independence (TABLE II)"


@unittest.skipUnless(HAS_STREAMLIT, "streamlit not installed")
class AppUITest(unittest.TestCase):
    def test_example_flow_in_mock_mode(self):
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
        at.run()
        self.assertFalse(at.exception)
        at.sidebar.radio[0].set_value("mock")
        at.sidebar.selectbox[0].set_value(EXAMPLE).run()
        self.assertFalse(at.exception)

        next(b for b in at.button if b.label == "Extract checklist").click().run()
        self.assertFalse(at.exception)
        self.assertGreaterEqual(len(at.expander), 12)

        next(b for b in at.button if b.label == "Check results").click().run()
        self.assertFalse(at.exception)
        self.assertIn("Overall", [m.label for m in at.metric])

    def _extract(self, at):
        at.run()
        at.sidebar.radio[0].set_value("mock")
        at.sidebar.selectbox[0].set_value(EXAMPLE).run()
        next(b for b in at.button if b.label == "Extract checklist").click().run()
        self.assertFalse(at.exception)
        return at.session_state["checklist"]

    def test_evidence_quotes_offer_source_text(self):
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
        self._extract(at)
        labels = [e.label for e in at.expander]
        self.assertIn("Show source text", labels)

    def test_continue_review_restores_saved_decisions(self):
        from repcheck.exporter import checklist_to_json
        from repcheck.schemas import ReviewStatus
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
        cl = self._extract(at)
        first = next(i for i in cl.items if i.required)
        saved = json.loads(checklist_to_json(cl))
        target = next(i for i in saved["items"] if i["key"] == first.key)
        target["review_status"] = ReviewStatus.CONFIRMED.value
        target["user_note"] = "checked against the paper"

        up = next(u for u in at.file_uploader if u.label == "Continue a saved review (.json)")
        up.set_value(("checklist.json", json.dumps(saved).encode(), "application/json")).run()
        self.assertFalse(at.exception)

        restored = at.session_state["checklist"]
        self.assertIsNot(restored, cl)
        item = restored.get(first.key)
        self.assertEqual(item.review_status, ReviewStatus.CONFIRMED)
        self.assertEqual(item.user_note, "checked against the paper")
        self.assertEqual(restored.content_hash, cl.content_hash)
        self.assertFalse([w for w in at.warning if "different paper" in w.value])

    def test_continue_review_warns_on_fingerprint_mismatch(self):
        from repcheck.exporter import checklist_to_json
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
        cl = self._extract(at)
        payload = checklist_to_json(cl)

        at.sidebar.selectbox[0].set_value(EXAMPLE_2).run()
        self.assertFalse(at.exception)
        up = next(u for u in at.file_uploader if u.label == "Continue a saved review (.json)")
        up.set_value(("checklist.json", payload.encode(), "application/json")).run()
        self.assertFalse(at.exception)

        warnings = [w.value for w in at.warning]
        self.assertTrue(any("different paper" in w for w in warnings))
        self.assertEqual(at.session_state["checklist"].source_file, cl.source_file)

    def test_continue_review_rejects_broken_json(self):
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
        self._extract(at)
        up = next(u for u in at.file_uploader if u.label == "Continue a saved review (.json)")
        up.set_value(("checklist.json", b'{"items": "not a checklist"}', "application/json")).run()
        self.assertFalse(at.exception)
        self.assertTrue([e for e in at.error if "Could not read" in e.value])


if __name__ == "__main__":
    unittest.main()
