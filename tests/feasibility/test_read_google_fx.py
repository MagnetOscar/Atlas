"""Synthetic parser checks only; no network, quotes or provider credentials."""

import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[2] / "scripts/feasibility/read_google_fx.py"
SPEC = importlib.util.spec_from_file_location("google_fx_feasibility", SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def parse(html, pair="USD-CNY"):
    parser = MODULE.QuoteAttributes()
    parser.feed(html)
    return MODULE.extract_visible_quote(parser, pair)


def block(pair="USD / CNY", rate="1.2345", timestamp=True):
    ending = "<div>Nov 1, 12:00:00 AM UTC</div>" if timestamp else ""
    return f"<h1>{pair}</h1><div>Example currencies</div><div>{rate}</div>{ending}"


class QuoteIdentityChecks(unittest.TestCase):
    def test_unrelated_asset_is_not_the_main_quote(self):
        result = parse("<nav><span>9876.5432</span></nav>" + block())
        self.assertEqual(result["rate"], "1.2345")
        self.assertEqual(result["quote_time_display"], "Nov 1, 12:00:00 AM UTC")

    def test_other_currency_pair_is_rejected(self):
        self.assertIsNone(parse(block("EUR / CNY")))

    def test_missing_quote_time_is_rejected(self):
        self.assertIsNone(parse(block(timestamp=False)))

    def test_ambiguous_duplicate_quote_is_rejected(self):
        self.assertIsNone(parse(block() + block(rate="2.3456")))

    def test_zero_or_negative_quotes_are_rejected(self):
        for value in ("0.0000", "-1.2345"):
            with self.subTest(value=value):
                self.assertIsNone(parse(block(rate=value)))

    def test_script_payload_is_not_visible_quote_evidence(self):
        payload = "<script>USD / CNY 5555.0000 Nov 1, 12:00:00 AM UTC</script>"
        self.assertIsNone(parse(payload))
        self.assertEqual(parse(payload + block())["rate"], "1.2345")


if __name__ == "__main__":
    unittest.main()
