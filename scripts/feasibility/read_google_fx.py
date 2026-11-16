"""One-shot, read-only Google Finance HTML feasibility check.

Uses no account, cookies, browser automation, database or persistent cache.
Does not install a scheduler or implement a supported production data source.
Run only where the intended use is permitted by the data provider's terms.
Output is diagnostic; do not commit live quote data to the public repository.
"""

import datetime as dt
import decimal
import gzip
import hashlib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

MAX_BYTES = 4 * 1024 * 1024
DESKTOP_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"


class QuoteAttributes(HTMLParser):
    def __init__(self):
        super().__init__()
        self.candidates = []
        self.titles = []
        self.in_title = False
        self.stack = []
        self.visible_numbers = []
        self.visible_utc_times = []
        self.recent_text = []
        self.time_contexts = []

    def handle_starttag(self, tag, attrs):
        row = dict(attrs)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append((tag, row))
        if tag == "title":
            self.in_title = True
        if "data-last-price" in row:
            self.candidates.append(
                {key: value for key, value in row.items() if key.startswith("data-")}
            )

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, value):
        if self.in_title:
            self.titles.append(value)
        text = value.strip()
        if not any(tag in {"script", "style", "title"} for tag, _ in self.stack):
            if text and len(text) < 160:
                self.recent_text.append(text)
                self.recent_text = self.recent_text[-24:]
            if re.fullmatch(r"[0-9][0-9,]*\.[0-9]+", text) and len(self.visible_numbers) < 12:
                self.visible_numbers.append({"text": text, "parents": [
                    {"tag": tag, "attributes": {key: str(item)[:120] for key, item in attrs.items() if key in {"class", "role", "aria-label"}}}
                    for tag, attrs in self.stack[-2:]
                ]})
            if "UTC" in text and len(text) < 160 and len(self.visible_utc_times) < 8:
                self.visible_utc_times.append(text)
                self.time_contexts.append({"text_before_time": list(self.recent_text), "parents": [
                    {"tag": tag, "attributes": {key: str(item)[:120] for key, item in attrs.items() if key in {"class", "role", "aria-label"}}}
                    for tag, attrs in self.stack[-5:]
                ]})


def extract_visible_quote(parser, pair):
    normalized_pair = pair.replace("-", "/")
    extracted = []
    for context in parser.time_contexts:
        text = context["text_before_time"]
        anchors = [index for index, value in enumerate(text) if value.replace(" ", "") == normalized_pair]
        if not anchors:
            continue
        for value in text[anchors[-1] + 1:-1]:
            if re.fullmatch(r"[0-9][0-9,]*\.[0-9]+", value):
                number = decimal.Decimal(value.replace(",", ""))
                if number.is_finite() and number > 0:
                    extracted.append({"rate": str(number), "quote_time_display": text[-1]})
                break
    return extracted[0] if len(extracted) == 1 else None


def inspect_pair(pair, desktop_agent=False, inspect_layout=False):
    if not re.fullmatch(r"[A-Z]{3}-[A-Z]{3}", pair):
        raise ValueError("Pair must be an ISO-style currency pair, e.g. USD-CNY")
    url = "https://www.google.com/finance/quote/" + pair + "?hl=en"
    row = {"pair": pair, "requested_url": url, "read_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "user_agent_mode": "desktop-compatibility-check" if desktop_agent else "identified-diagnostic"}
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": DESKTOP_AGENT if desktop_agent else "KomariPersonalFeasibility/0.1",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            row.update(status=response.status, final_url=response.url, content_type=response.headers.get("Content-Type"))
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ValueError("Response exceeds diagnostic size limit")
            row["downloaded_bytes"] = len(body)
            if response.headers.get("Content-Encoding", "").lower() == "gzip":
                body = gzip.decompress(body)
            if len(body) > MAX_BYTES:
                raise ValueError("Decoded response exceeds diagnostic size limit")
            final = urllib.parse.urlsplit(response.url)
            destination_ok = final.scheme == "https" and final.hostname == "www.google.com" and final.path == "/finance/quote/" + pair
            row["body_sha256"] = hashlib.sha256(body).hexdigest()
            parser = QuoteAttributes()
            parser.feed(body.decode(response.headers.get_content_charset() or "utf-8", errors="replace"))
        row["title"] = "".join(parser.titles)
        if inspect_layout:
            row["legacy_quote_attributes"] = parser.candidates
            row["visible_decimal_candidates"] = parser.visible_numbers
            row["visible_utc_timestamps"] = parser.visible_utc_times
            row["time_contexts"] = parser.time_contexts
        row["expected_destination"] = destination_ok
        normalized_pair = pair.replace("-", "/")
        extracted = extract_visible_quote(parser, pair)
        row["extraction_success"] = destination_ok and normalized_pair in row["title"] and extracted is not None
        if row["extraction_success"]:
            row["main_quote"] = extracted
            row["extraction_method"] = "visible pair anchor and main quote before UTC timestamp"
        row["note"] = "One-shot extraction proof, not a stable official API or a grant of data reuse rights."
    except Exception as error:
        row["error_type"] = type(error).__name__
        row["error"] = str(error)[:300]
        if isinstance(error, urllib.error.HTTPError):
            row["status"] = error.code
        row["extraction_success"] = False
    return row


if __name__ == "__main__":
    desktop_agent = "--desktop-agent" in sys.argv[1:]
    inspect_layout = "--inspect-layout" in sys.argv[1:]
    pairs = [arg for arg in sys.argv[1:] if arg not in {"--desktop-agent", "--inspect-layout"}] or ["USD-CNY", "EUR-CNY"]
    if len(pairs) > 4:
        raise SystemExit("At most four explicit pairs per one-shot diagnostic")
    now = dt.datetime.now(dt.timezone.utc)
    next_midnight = (now + dt.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    results = [inspect_pair(pair, desktop_agent, inspect_layout) for pair in pairs]
    print(json.dumps({
        "mode": "one-shot-read-only",
        "measured_at_utc": now.isoformat(),
        "planned_daily_schedule": "00:00 UTC",
        "next_utc_boundary": next_midnight.isoformat(),
        "scheduler_installed": False,
        "results": results,
    }, ensure_ascii=False))
    raise SystemExit(0 if all(row["extraction_success"] for row in results) else 1)
