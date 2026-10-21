"""
Reproducible measurement of Ground Truth's source-domain approval rule.

No API keys, no network, no database. Pure domain-classification logic as shipped
(loads docs/APPROVED_SOURCES.md).

RERUN:
    python -m pip install httpx pydantic pydantic-settings sqlalchemy structlog python-dotenv
    PYTHONPATH=. python scripts/measure_source_validator.py

Labels are assigned by the project's OWN stated policy (README 'Core Principles'):
  accept = primary authoritative gov / institutional / recognized academic source
  reject = news, encyclopedia, social media, or general commercial/blog content
"""
from groundtruth.verification.source_validator import SourceValidator

# (url, expected_accept, rationale): labels based on project policy
DATASET = [
    ("https://www.loc.gov/collections/", True, "Library of Congress"),
    ("https://www.archives.gov/research", True, "National Archives"),
    ("https://www.cia.gov/the-world-factbook/", True, "CIA World Factbook"),
    ("https://www.state.gov/reports/", True, "US State Dept"),
    ("https://api.congress.gov/v3/bill", True, "Congress.gov (subdomain)"),
    ("https://data.worldbank.org/indicator", True, "World Bank data"),
    ("https://www.sipri.org/databases", True, "SIPRI arms data"),
    ("https://fas.org/nuke/guide/", True, "Federation of American Scientists"),
    ("https://home.treasury.gov/policy-issues/financial-sanctions", True, "US Treasury (subdomain)"),
    ("https://www.defense.gov/News/", True, "US DoD"),
    ("https://acleddata.com/data-export-tool/", True, "ACLED conflict data"),
    ("https://www.gdeltproject.org/data.html", True, "GDELT"),
    ("https://ucdp.uu.se/encyclopedia", True, "UCDP (Uppsala)"),
    ("https://comtrade.un.org/data", True, "UN Comtrade"),
    ("https://www.icj-cij.org/case", True, "Int'l Court of Justice"),
    ("https://www.nationalarchives.gov.uk/documents/", True, "UK National Archives"),
    ("https://doi.org/10.1000/xyz", True, "DOI (academic)"),
    ("https://www.dni.gov/index.php/", True, "US DNI"),
    ("https://www.un.org/securitycouncil/", True, "UN primary (list-coverage probe)"),
    ("https://www.census.gov/data.html", True, "US Census (list-coverage probe)"),
    ("https://www.nasa.gov/mission", True, "NASA (list-coverage probe)"),
    ("https://www.bls.gov/data/", True, "US Bureau of Labor Statistics (probe)"),
    ("https://www.whitehouse.gov/briefing-room/", True, "White House (probe)"),
    ("https://en.wikipedia.org/wiki/NATO", False, "Wikipedia"),
    ("https://www.nytimes.com/2024/world", False, "NYT news"),
    ("https://www.bbc.com/news/world", False, "BBC news"),
    ("https://www.reuters.com/world/", False, "Reuters news"),
    ("https://twitter.com/statedept", False, "Twitter/X"),
    ("https://www.reddit.com/r/geopolitics", False, "Reddit"),
    ("https://medium.com/@analyst/post", False, "Medium blog"),
    ("https://substack.com/newsletter", False, "Substack"),
    ("https://www.cnn.com/world", False, "CNN news"),
    ("https://www.aljazeera.com/news/", False, "Al Jazeera news"),
    ("https://www.theguardian.com/world", False, "Guardian news"),
    ("https://www.washingtonpost.com/world/", False, "WaPo news"),
    ("https://example.com/report", False, "Generic commercial"),
    ("https://someconsultancy.com/whitepaper", False, "Consultant blog"),
    ("https://randomblog.org/opinion", False, "Personal blog"),
    ("https://www.chatham-analysis.net/take", False, "Unknown analysis site"),
]


def main():
    validator = SourceValidator()
    tp = fp = tn = fn = 0
    misses = []
    for url, expected, why in DATASET:
        approved, note = validator.check_domain_approved(url)
        if expected and approved:
            tp += 1
        elif (not expected) and (not approved):
            tn += 1
        elif (not expected) and approved:
            fp += 1
            misses.append(("FALSE ACCEPT", url, why, note))
        elif expected and (not approved):
            fn += 1
            misses.append(("MISSED (gap)", url, why, note))
    sample_count = len(DATASET)
    acc = (tp + tn) / sample_count
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    print(f"Approved-domains list loaded: {len(validator._approved_domains)} domains (docs/APPROVED_SOURCES.md)")
    print(f"Dataset: {sample_count} labeled URLs\n")
    print(f"  True Accept (TP): {tp}   False Accept (FP): {fp}")
    print(f"  True Reject (TN): {tn}   Missed/Gap  (FN): {fn}\n")
    print(f"  Accuracy : {acc:.1%}")
    print(f"  Precision: {prec:.1%}")
    print(f"  Recall   : {rec:.1%}")
    print(f"  F1       : {f1:.1%}\n")
    for kind, url, why, note in misses:
        print(f"  [{kind}] {url} -- {why}\n            validator: {note}")


if __name__ == "__main__":
    main()
