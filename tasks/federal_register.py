"""Federal Register documents from GovInfo's bulk XML (the Government Publishing Office's official channel).

Legal basis: 1 CFR 2.6, "Any person may reproduce or republish, without restriction, any material
appearing in any regular or special edition of the Federal Register." Documents are also works of the
US Government (17 U.S.C. 105). Shared by the fedreg_* tasks; daily files are cached in tasks/.sources/.
"""

import datetime as dt
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

CACHE = Path(__file__).resolve().parent / ".sources" / "federal_register"
SECTIONS = {"RULES": ("RULE", "Rule"), "PRORULES": ("PRORULE", "Proposed Rule"), "NOTICES": ("NOTICE", "Notice")}
FILED = re.compile(r"Filed (\d{1,2})-(\d{1,2})-(\d{2})")


def text(element) -> str:
    return " ".join("".join(element.itertext()).split()) if element is not None else ""


def issue(day: dt.date):
    """One day's Federal Register as XML, or None when there was no issue (weekends, holidays)."""
    path = CACHE / f"FR-{day}.xml"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        try:
            urllib.request.urlretrieve(f"https://www.govinfo.gov/bulkdata/FR/{day:%Y}/{day:%m}/FR-{day}.xml", path)
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return None
            raise
        time.sleep(1)
    return ET.parse(path).getroot()


def documents(first: dt.date, last: dt.date, filed_from: dt.date):
    """Rules, proposed rules and notices published first..last and filed on or after filed_from."""
    day = first
    while day <= last:
        root = issue(day)
        for section, (tag, kind) in SECTIONS.items():
            for doc in [] if root is None else root.findall(f".//{section}/{tag}"):
                frdoc = text(doc.find(".//FRDOC"))
                m = FILED.search(frdoc)
                number = re.search(r"\d{4}-\d{5}", frdoc)
                if not m or not number:
                    continue
                filed = dt.date(2000 + int(m.group(3)), int(m.group(1)), int(m.group(2)))
                if filed < filed_from:
                    continue
                yield {"id": f"fr-{number.group(0)}", "published": str(day), "filed": str(filed), "kind": kind,
                       "agency": text(doc.find(".//AGENCY")), "subagency": text(doc.find(".//SUBAGY")),
                       "subject": text(doc.find(".//SUBJECT")), "action": text(doc.find(".//ACT")),
                       "summary": re.sub(r"^SUMMARY:\s*", "", text(doc.find(".//SUM")))}
        day += dt.timedelta(days=1)


def mask(value: str, terms, token: str) -> str:
    """Replace every whole-word occurrence of the terms, longest first, ignoring case."""
    for term in sorted({t for t in terms if t}, key=len, reverse=True):
        value = re.sub(rf"(?<!\w){re.escape(term)}(?!\w)", token, value, flags=re.I)
    return value
