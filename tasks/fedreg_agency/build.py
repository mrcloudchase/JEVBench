"""Build fedreg_agency: which department or agency issued this Federal Register document?

The label is the issuing agency named in the document's own header. The evidence is the subject and
summary with every listed agency's and component's name and acronym masked as [agency], in every document
alike, so the masking itself carries no clue. The ten agencies
with the most documents in the window, filed September 28 - October 17, 2026; up to 100 per agency with seed 7.

    python -m tdm build fedreg_agency
"""
import collections
import datetime as dt
import json
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from federal_register import documents, mask  # noqa: E402

AGENCIES = {   # label: (header name, description, names and acronyms of the agency and its components to mask)
    "transportation": ("DEPARTMENT OF TRANSPORTATION", "Department of Transportation (aviation, highways, rail, pipelines, vehicles, shipping)",
                       ["DOT", "FAA", "Federal Aviation Administration", "FMCSA", "NHTSA", "PHMSA", "FRA", "FTA", "FHWA", "MARAD",
                        "Maritime Administration", "Federal Railroad Administration", "Federal Transit Administration", "Federal Highway Administration",
                        "Federal Motor Carrier Safety Administration", "National Highway Traffic Safety Administration",
                        "Pipeline and Hazardous Materials Safety Administration"]),
    "commerce": ("DEPARTMENT OF COMMERCE", "Department of Commerce (trade, fisheries and oceans, patents, standards, census, export controls)",
                 ["DOC", "NOAA", "NMFS", "National Oceanic and Atmospheric Administration", "National Marine Fisheries Service",
                  "International Trade Administration", "ITA", "Bureau of Industry and Security", "BIS", "USPTO", "Patent and Trademark Office",
                  "NIST", "National Institute of Standards and Technology", "Census Bureau", "Bureau of the Census", "Enforcement and Compliance"]),
    "health": ("DEPARTMENT OF HEALTH AND HUMAN SERVICES", "Department of Health and Human Services (drugs, medical devices, Medicare and Medicaid, public health)",
               ["HHS", "FDA", "Food and Drug Administration", "CMS", "Centers for Medicare & Medicaid Services",
                "Centers for Medicare and Medicaid Services", "CDC", "Centers for Disease Control and Prevention", "NIH", "National Institutes of Health",
                "HRSA", "SAMHSA", "ACF", "Administration for Children and Families", "Indian Health Service", "IHS"]),
    "homeland_security": ("DEPARTMENT OF HOMELAND SECURITY", "Department of Homeland Security (immigration, borders, Coast Guard, emergencies, transportation security)",
                          ["DHS", "USCIS", "U.S. Citizenship and Immigration Services", "CBP", "U.S. Customs and Border Protection",
                           "ICE", "FEMA", "Federal Emergency Management Agency", "TSA", "Transportation Security Administration", "Coast Guard",
                           "USCG", "CISA", "Cybersecurity and Infrastructure Security Agency"]),
    "interior": ("DEPARTMENT OF THE INTERIOR", "Department of the Interior (public lands, parks, wildlife, tribes, energy and minerals on federal land)",
                 ["DOI", "BLM", "Bureau of Land Management", "NPS", "National Park Service", "FWS", "USFWS", "Fish and Wildlife Service",
                  "BOEM", "BSEE", "BIA", "Bureau of Indian Affairs", "USGS", "Geological Survey", "Bureau of Reclamation", "Office of Surface Mining Reclamation and Enforcement", "OSMRE"]),
    "treasury": ("DEPARTMENT OF THE TREASURY", "Department of the Treasury (taxes, banking, sanctions, financial crimes)",
                 ["IRS", "Internal Revenue Service", "OCC", "Comptroller of the Currency", "FinCEN", "Financial Crimes Enforcement Network",
                  "OFAC", "Office of Foreign Assets Control", "TTB", "Alcohol and Tobacco Tax and Trade Bureau", "Fiscal Service"]),
    "defense": ("DEPARTMENT OF DEFENSE", "Department of Defense (military, defense acquisition, Army Corps of Engineers)",
                ["DoD", "DOD", "Department of War", "DoW", "USACE", "Corps of Engineers",
                 "Defense Logistics Agency", "DLA", "Defense Acquisition Regulations System", "DARS"]),
    "justice": ("DEPARTMENT OF JUSTICE", "Department of Justice (law enforcement, drugs, firearms, prisons, courts)",
                ["DOJ", "DEA", "Drug Enforcement Administration", "FBI", "Federal Bureau of Investigation", "ATF",
                 "Bureau of Alcohol, Tobacco, Firearms, and Explosives", "Bureau of Prisons", "BOP", "U.S. Marshals Service", "Antitrust Division"]),
    "environment": ("ENVIRONMENTAL PROTECTION AGENCY", "Environmental Protection Agency (air and water quality, chemicals, pesticides, waste)",
                    ["Environmental Protection Agency", "EPA"]),
    "labor": ("DEPARTMENT OF LABOR", "Department of Labor (workplace safety, wages, pensions and benefits, employment and training)",
              ["DOL", "OSHA", "Occupational Safety and Health Administration", "EBSA", "Employee Benefits Security Administration",
               "Employment and Training Administration", "ETA", "MSHA", "Mine Safety and Health Administration", "Wage and Hour Division", "WHD", "OFCCP"]),
}
PER_AGENCY = 100                # or all when fewer
GENERIC = re.compile(r"\b(Department|Secretary|Office of the Secretary) of (the )?(Transportation|Commerce|Health and Human Services|Homeland Security|"
                     r"(the )?Interior|(the )?Treasury|Defense|War|Justice|Labor)\b", re.I)

header = {v[0]: k for k, v in AGENCIES.items()}
ALL_TERMS = [t for v in AGENCIES.values() for t in v[2]] + ["Department of the Army", "Department of the Navy", "Department of the Air Force"]
docs = [d for d in documents(dt.date(2026, 9, 28), dt.date(2026, 10, 17), dt.date(2026, 9, 28))
        if len(d["summary"]) >= 200 and d["agency"] in header]
rng = random.Random(7)
rows = []
for label, (name, _, _) in AGENCIES.items():
    group = [d for d in docs if d["agency"] == name]
    rng.shuffle(group)
    print(f"{label}: {len(group)} available")
    for d in group[:PER_AGENCY]:
        own = ALL_TERMS + [d["subagency"].title(), d["subagency"]]
        clean = lambda s: GENERIC.sub("[agency]", mask(s, own, "[agency]"))
        rows.append({"id": d["id"], "state": {"subject": clean(d["subject"]), "summary": clean(d["summary"])},
                     "label": label, "kind": d["kind"], "published": d["published"], "filed": d["filed"]})
rng.shuffle(rows)
with open(HERE / "data.jsonl", "w", encoding="utf-8") as f:
    f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
with open(HERE / "manifest.jsonl", "w", encoding="utf-8") as f:
    f.writelines(json.dumps({k: v for k, v in r.items() if k != "state"}) + "\n" for r in rows)
lines = ["# One 10-way choice question. The label is the issuing agency in the document's header; agency names are masked.",
         "agency:", "  type: choice", "  instructions: Which department or agency issued this Federal Register document?", "  criteria:"]
lines += [f"    {k}: {v[1]}" for k, v in AGENCIES.items()]
(HERE / "questions.yaml").write_text("\n".join(lines) + "\n")
print(f"{len(rows)} records; {collections.Counter(r['kind'] for r in rows)}")
