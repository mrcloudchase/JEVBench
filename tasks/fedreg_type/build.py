"""Build fedreg_type: is this Federal Register document a rule, a proposed rule or a notice?

The label is the section the Office of the Federal Register published it in, which follows the issuing
agency's own designation. The evidence is the subject and summary; the ACTION line and phrases that name
the document type ("final rule", "proposed rulemaking", "this notice") are masked as [document].
Documents filed September 28 - October 17, 2026; up to 300 of each type with seed 7, all of a type when fewer.

    python -m tdm build fedreg_type
"""
import datetime as dt
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from federal_register import documents, mask  # noqa: E402

PER_TYPE = 300                  # or all when fewer: there are 161 rules and 98 proposed rules
TYPE_WORDS = ["proposed regulations", "proposed regulation", "final regulations", "final regulation", "temporary regulations",
              "proposed amendments", "proposed amendment", "final amendments", "final amendment", "interim final rule", "direct final rule", "final rule", "final rules", "proposed rule", "proposed rules",
              "notice of proposed rulemaking", "advance notice of proposed rulemaking", "proposed rulemaking", "rulemaking",
              "NPRM", "ANPRM", "this rule", "the rule", "this notice", "the notice", "notice", "notices", "rule", "rules"]

docs = [d for d in documents(dt.date(2026, 9, 28), dt.date(2026, 10, 17), dt.date(2026, 9, 28)) if len(d["summary"]) >= 200]
rng = random.Random(7)
rows = []
for kind in ("Rule", "Proposed Rule", "Notice"):
    group = [d for d in docs if d["kind"] == kind]
    rng.shuffle(group)
    print(f"{kind}: {len(group)} available")
    rows += [{"id": d["id"], "state": {"subject": mask(d["subject"], TYPE_WORDS, "[document]"),
                                       "summary": mask(d["summary"], TYPE_WORDS, "[document]")},
              "label": kind.lower().replace(" ", "_"), "agency": d["agency"], "published": d["published"], "filed": d["filed"]}
             for d in group[:PER_TYPE]]
rng.shuffle(rows)
with open(HERE / "data.jsonl", "w", encoding="utf-8") as f:
    f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
with open(HERE / "manifest.jsonl", "w", encoding="utf-8") as f:
    f.writelines(json.dumps({k: v for k, v in r.items() if k != "state"}) + "\n" for r in rows)
(HERE / "questions.yaml").write_text("""# One 3-way choice question. The label is the section the Federal Register published the document in.
type:
  type: choice
  instructions: What kind of Federal Register document is this?
  criteria:
    rule: A final rule, which changes regulations and has legal effect
    proposed_rule: A proposed rule, which asks for public comment on a planned regulatory change
    notice: A notice, which announces information such as meetings, applications, decisions or requests for comment
""")
print(f"{len(rows)} records")
