"""Step 1: build a company-by-year panel of NGER corporate emissions.

Reads the nine NGER corporate CSVs (2016-17 to 2024-25) published by the Clean
Energy Regulator, keeps the five ASX energy producers in scope, and writes
data/processed/corporate_panel.csv.

Run:  python3 -I src/01_corporate_panel.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "cer"
OUT = ROOT / "data" / "processed"

# Regex on the upper-cased organisation name -> short company label.
COMPANIES = {
    "Woodside": r"^WOODSIDE",
    # From 2023-24 the Curtis Island GLNG plant (about 1.6 Mt a year) is reported by
    # GLNG Operations Pty Ltd, a 30%-owned joint venture, not by Santos Limited. Before
    # then Santos Limited reported the plant itself. Including GLNG Operations keeps
    # the Santos series like-for-like. See the README for the alternative.
    "Santos": r"^(?:SANTOS\b|GLNG OPERATIONS\b)",
    "Origin": r"^ORIGIN ENERGY\b",
    "AGL": r"^AGL ENERGY\b",
    "Beach": r"^BEACH ENERGY\b",
}


def to_number(x):
    """'30,439,497' -> 30439497.0; '-' or blanks -> NaN."""
    if pd.isna(x):
        return float("nan")
    s = str(x).replace(",", "").strip()
    return pd.to_numeric(s, errors="coerce")


def load_year(path: Path) -> pd.DataFrame:
    year = re.search(r"(\d{4}-\d{2})", path.name).group(1)
    # Most files are UTF-8 (one has a BOM); a few carry stray Windows-1252 bytes.
    try:
        df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="cp1252", dtype=str)
    # Column names change in case between years, so match on lower-case text.
    cols = {c: c.strip().lower() for c in df.columns}
    df = df.rename(columns=cols)
    # The first column is the company name, but it was called "Controlling
    # Corporation" in 2016-17 and "Organisation name" afterwards.
    name_col = df.columns[0]
    s1 = next(c for c in df.columns if c.startswith("total scope 1"))
    s2 = next(c for c in df.columns if c.startswith("total scope 2"))
    en = next(c for c in df.columns if c.startswith("net energy"))
    out = pd.DataFrame({
        "year": year,
        "name": df[name_col].str.strip(),
        "scope1_t": df[s1].map(to_number),
        "scope2_t": df[s2].map(to_number),
        "energy_gj": df[en].map(to_number),
    })
    return out.dropna(subset=["name"])


def main():
    frames = [load_year(p) for p in sorted(RAW.glob("nger-corporate-*.csv"))]
    allrows = pd.concat(frames, ignore_index=True)
    upper = allrows["name"].str.upper()

    parts = []
    for label, pattern in COMPANIES.items():
        hit = allrows[upper.str.contains(pattern, regex=True)].copy()
        hit["company"] = label
        parts.append(hit)
    panel = pd.concat(parts, ignore_index=True)

    print("Matched names (check nothing is missing or wrongly included):")
    print(panel.groupby(["company", "name"]).year.agg(["count", "min", "max"]).to_string())

    # Where a group reports through more than one entity in a year (Santos Limited
    # plus GLNG Operations from 2023-24), add them together and say so.
    dup = panel.groupby(["company", "year"]).size()
    if (dup > 1).any():
        print("\nNote: combining several entities into one company-year row for:")
        print(panel[panel.set_index(["company", "year"]).index.isin(dup[dup > 1].index)]
              [["company", "year", "name", "scope1_t"]].to_string(index=False))
    panel = (panel.groupby(["company", "year"], as_index=False)
             .agg(name=("name", " + ".join), scope1_t=("scope1_t", "sum"),
                  scope2_t=("scope2_t", "sum"), energy_gj=("energy_gj", "sum")))

    panel = panel.sort_values(["company", "year"])
    OUT.mkdir(parents=True, exist_ok=True)
    panel.to_csv(OUT / "corporate_panel.csv", index=False)

    print("\nScope 1 emissions (Mt CO2-e):")
    print((panel.pivot(index="year", columns="company", values="scope1_t") / 1e6).round(2).to_string())
    print("\nYears present per company:")
    print(panel.groupby("company").year.nunique().to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
