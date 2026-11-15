"""Headless test of the Streamlit interface (runs only where streamlit is installed)."""
import importlib.util
import unittest

from helpers import ROOT

HAS_STREAMLIT = importlib.util.find_spec("streamlit") is not None
EXAMPLE = "Example 1 — analyst coverage (Table 3)"


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


if __name__ == "__main__":
    unittest.main()
