"""Step 2: build a facility-by-year panel from the Safeguard Mechanism data.

The Clean Energy Regulator changed the layout of its Safeguard tables in 2023-24
(when the reformed, declining baselines began), so this script harmonises the
two layouts into one set of columns, keeps the facilities run by the five
companies in scope, and writes:

  data/processed/facility_panel.csv    one row per facility-year
  data/processed/company_safeguard.csv one row per company-year

Run:  python3 -I src/02_safeguard_panel.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "cer"
OUT = ROOT / "data" / "processed"

# Responsible-emitter names start with the group name (subsidiaries included).
COMPANIES = {
    "Woodside": r"^WOODSIDE",
    "Santos": r"^SANTOS\b",
    "Origin": r"^ORIGIN ENERGY\b",
    "AGL": r"^AGL\b",
    "Beach": r"^BEACH ENERGY\b",
}

ACCU_COLS = ["accus_issued", "accus_deemed_surrendered", "accus_surrendered", "smcs_surrendered"]


def to_number(x):
    """' 129,354 ' -> 129354.0 ; '-', 'n/a', blank -> NaN."""
    if pd.isna(x):
        return float("nan")
    s = str(x).replace(",", "").strip()
    return pd.to_numeric(s, errors="coerce")


def read_csv(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="cp1252", dtype=str)
    df.columns = [re.sub(r"\s+", " ", c).strip().lower() for c in df.columns]
    return df


def pick(cols, include, exclude=()):
    """First column whose name contains every `include` word and no `exclude` word."""
    for c in cols:
        if all(w in c for w in include) and not any(w in c for w in exclude):
            return c
    return None


def load_year(path: Path) -> pd.DataFrame:
    year = re.search(r"(\d{4}-\d{2})", path.name).group(1)
    df = read_csv(path)
    cols = list(df.columns)
    skip = ("mymp", "multi", "cumulative", "type")

    m = {
        "facility": cols[0],
        "emitter": pick(cols, ["responsible emitter"], ["abn"]),
        "state": pick(cols, ["state"]),
        "baseline": pick(cols, ["baseline", "number"], skip) or pick(cols, ["baseline emissions"], skip),
        "covered": pick(cols, ["covered emissions"]),
        "accus_issued": pick(cols, ["issued"], ["smc"]),
        "accus_deemed_surrendered": pick(cols, ["deemed"]),
        "accus_surrendered": pick(cols, ["surrendered"], ["deemed", "smc"])
        or pick(cols, ["units surrendered"], ["deemed"]),
        "smcs_surrendered": pick(cols, ["smcs surrendered"]),
        "net_emissions": pick(cols, ["net emissions number"], skip),
    }
    out = pd.DataFrame({"year": year}, index=df.index)
    for new, old in m.items():
        out[new] = df[old] if old else pd.NA
    for c in ["baseline", "covered", "net_emissions"] + ACCU_COLS:
        out[c] = out[c].map(to_number)
    # A dash in a credit column means none were issued or surrendered.
    for c in ACCU_COLS:
        out[c] = out[c].fillna(0.0)
    out["emitter"] = out["emitter"].astype("string").str.strip()
    return out.dropna(subset=["facility"])


def main():
    paths = sorted(p for p in RAW.glob("*.csv")
                   if p.name.startswith("safeguard-facilities-data")
                   or "baselines-and-emissions-table" in p.name
                   and "safeguard-baselines" not in p.name)
    frames = [load_year(p) for p in paths]
    allrows = pd.concat(frames, ignore_index=True)
    print("Files read:", len(paths), "| facility-years:", len(allrows))

    upper = allrows["emitter"].fillna("").str.upper()
    parts = []
    for label, pattern in COMPANIES.items():
        hit = allrows[upper.str.contains(pattern, regex=True)].copy()
        hit["company"] = label
        parts.append(hit)
    fac = pd.concat(parts, ignore_index=True).sort_values(["company", "year", "facility"])

    print("\nResponsible-emitter names matched (check each belongs to its group):")
    print(fac.groupby(["company", "emitter"]).year.agg(["count", "min", "max"]).to_string())

    OUT.mkdir(parents=True, exist_ok=True)
    fac.to_csv(OUT / "facility_panel.csv", index=False)

    # Facilities on a multi-year monitoring period report "n/a" for baseline and
    # net emissions in the old layout. Summing would silently drop them, so a
    # total is only reported when every facility in the group has a value.
    def complete_sum(s):
        return s.sum() if s.notna().all() else float("nan")

    g = fac.groupby(["company", "year"])
    summ = g.agg(
        facilities=("facility", "nunique"),
        baseline_t=("baseline", complete_sum),
        covered_t=("covered", "sum"),
        net_t=("net_emissions", complete_sum),
        accus_issued=("accus_issued", "sum"),
        accus_deemed=("accus_deemed_surrendered", "sum"),
        accus_surrendered=("accus_surrendered", "sum"),
        smcs_surrendered=("smcs_surrendered", "sum"),
    ).reset_index()
    summ.to_csv(OUT / "company_safeguard.csv", index=False)

    pd.set_option("display.width", 200)
    show = summ.copy()
    for c in ["baseline_t", "covered_t", "net_t", "accus_issued", "accus_deemed", "accus_surrendered", "smcs_surrendered"]:
        show[c] = (show[c] / 1e6).round(2)
    print("\nSafeguard totals per company-year (Mt CO2-e or million units):")
    print(show.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
