"""Step 3: charts and the table behind them.

Reads data/processed/*.csv (made by steps 1 and 2) and writes three PNGs to
figures/ plus figures/summary_table.csv.

Run:  python3 -I src/03_charts.py
"""
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
FIG = ROOT / "figures"

# Surface and ink (light mode). Colour follows the company, never its rank.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e6e5e1"
COLOUR = {
    "AGL": "#2a78d6",
    "Beach": "#eb6834",
    "Origin": "#1baf7a",
    "Santos": "#eda100",
    "Woodside": "#e87ba4",
}
SOURCE = "Source: Clean Energy Regulator (NGER corporate and Safeguard Mechanism data)."


def setup(fig, ax, title, subtitle):
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    ax.grid(axis="y", color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    fig.text(0.06, 0.95, title, fontsize=14, fontweight="bold", color=INK, ha="left", va="top")
    fig.text(0.06, 0.895, subtitle, fontsize=9.5, color=INK2, ha="left", va="top")


def footer(fig, extra=""):
    text = textwrap.fill((extra + " " + SOURCE).strip(), 120)
    fig.text(0.06, 0.02, text, fontsize=8, color=INK2, ha="left", va="bottom", linespacing=1.4)


def spread(values, min_gap):
    """Nudge label y-positions apart so end labels do not collide."""
    order = sorted(values, key=values.get)
    pos = dict(values)
    for _ in range(50):
        moved = False
        for a, b in zip(order, order[1:]):
            if pos[b] - pos[a] < min_gap:
                mid = (pos[a] + pos[b]) / 2
                pos[a], pos[b] = mid - min_gap / 2, mid + min_gap / 2
                moved = True
        if not moved:
            break
    return pos


def chart1_index(corp):
    """Scope 1 emissions, 2017-18 = 100."""
    base_year = "2017-18"  # Beach has no 2016-17 row, so all five start here.
    p = corp.pivot(index="year", columns="company", values="scope1_t")
    p = p.loc[p.index >= base_year]
    idx = p / p.loc[base_year] * 100

    fig, ax = plt.subplots(figsize=(9, 5.6))
    fig.subplots_adjust(left=0.08, right=0.84, top=0.80, bottom=0.24)
    setup(fig, ax, "AGL cut Scope 1 emissions the most; Beach was the only one to rise",
          "Scope 1 emissions by company, indexed to 2017-18 = 100 (NGER, Australian operations)")
    x = range(len(idx))
    ax.axhline(100, color=INK2, linewidth=1, zorder=1)
    for c in idx.columns:
        ax.plot(x, idx[c], color=COLOUR[c], linewidth=2, solid_capstyle="round", solid_joinstyle="round", zorder=3, label=c)
        ax.scatter([len(idx) - 1], [idx[c].iloc[-1]], s=60, color=COLOUR[c], edgecolor=SURFACE, linewidth=2, zorder=4)
    ends = spread({c: idx[c].iloc[-1] for c in idx.columns}, 5.5)
    for c in idx.columns:
        ax.text(len(idx) - 1 + 0.2, ends[c], f"{c}  {idx[c].iloc[-1]:.0f}", color=INK, fontsize=10, va="center")
    ax.set_xticks(list(x))
    ax.set_xticklabels(idx.index, rotation=0)
    ax.set_ylim(40, 150)
    ax.set_yticks([40, 60, 80, 100, 120, 140])
    ax.set_xlim(-0.2, len(idx) - 1 + 0.2)
    ax.legend(loc="lower left", frameon=False, fontsize=9, labelcolor=INK2, ncol=5, bbox_to_anchor=(0, -0.2), handlelength=1.4)
    footer(fig, "Santos includes GLNG Operations from 2023-24 (see README). Emissions are not adjusted for production, acquisitions or asset sales.")
    fig.savefig(FIG / "fig1_scope1_index.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return idx


def chart2_baseline(sg):
    """Covered emissions as a share of the Safeguard baseline, after the 2023 reform."""
    d = sg[sg.year.isin(["2023-24", "2024-25"]) & sg.baseline_t.notna()].copy()
    d["ratio"] = d.covered_t / d.baseline_t * 100
    order = d[d.year == "2024-25"].sort_values("ratio")["company"].tolist()

    fig, ax = plt.subplots(figsize=(9, 4.6))
    fig.subplots_adjust(left=0.14, right=0.93, top=0.76, bottom=0.26)
    setup(fig, ax, "Woodside and Beach were over their Safeguard baselines in both years",
          "Covered emissions as % of baseline, summed across each company's facilities (above 100% = over baseline)")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, linewidth=1)
    ax.axvline(100, color=INK2, linewidth=1, zorder=1)
    for i, c in enumerate(order):
        r = d[d.company == c].set_index("year")["ratio"]
        ax.plot([r["2023-24"], r["2024-25"]], [i, i], color=COLOUR[c], linewidth=2, zorder=2)
        ax.scatter([r["2023-24"]], [i], s=70, facecolor=SURFACE, edgecolor=COLOUR[c], linewidth=2, zorder=3)
        ax.scatter([r["2024-25"]], [i], s=70, color=COLOUR[c], edgecolor=SURFACE, linewidth=2, zorder=4)
        right = max(r["2023-24"], r["2024-25"])
        ax.text(right + 3, i, f"{r['2023-24']:.0f}% → {r['2024-25']:.0f}%", va="center", fontsize=10, color=INK)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order, fontsize=10, color=INK)
    ax.set_xlim(50, 160)
    ax.set_xlabel("Hollow dot = 2023-24, filled dot = 2024-25", fontsize=9, color=INK2, loc="left")
    footer(fig, "Net across facilities; the obligation applies facility by facility. Origin's Safeguard facilities are about 4% of its emissions.")
    fig.savefig(FIG / "fig2_vs_baseline.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return d


def chart3_credits(sg):
    """Credits surrendered as a share of covered emissions."""
    d = sg[sg.company.isin(["Woodside", "Santos", "Beach"]) & (sg.year >= "2022-23")].copy()
    d["credits_pct"] = (d.accus_surrendered + d.accus_deemed + d.smcs_surrendered) / d.covered_t * 100
    p = d.pivot(index="year", columns="company", values="credits_pct")

    fig, ax = plt.subplots(figsize=(9, 5.2))
    fig.subplots_adjust(left=0.08, right=0.84, top=0.80, bottom=0.24)
    setup(fig, ax, "Only Woodside's credit use rose every year since 2022-23",
          "Carbon credits surrendered as % of covered emissions (ACCUs and SMCs)")
    x = range(len(p))
    for c in p.columns:
        ax.plot(x, p[c], color=COLOUR[c], linewidth=2, solid_capstyle="round", solid_joinstyle="round", zorder=3, label=c)
        ax.scatter(list(x), p[c], s=60, color=COLOUR[c], edgecolor=SURFACE, linewidth=2, zorder=4)
    ends = spread({c: p[c].iloc[-1] for c in p.columns}, 1.6)
    for c in p.columns:
        ax.text(len(p) - 1 + 0.08, ends[c], f"{c}  {p[c].iloc[-1]:.0f}%", color=INK, fontsize=10, va="center")
    ax.set_xticks(list(x))
    ax.set_xticklabels(p.index)
    ax.set_ylim(0, 30)
    ax.set_yticks([0, 10, 20, 30])
    ax.set_yticklabels(["0%", "10%", "20%", "30%"])
    ax.set_xlim(-0.1, len(p) - 1 + 0.1)
    ax.legend(loc="lower left", frameon=False, fontsize=9, labelcolor=INK2, ncol=3, bbox_to_anchor=(0, -0.2), handlelength=1.4)
    footer(fig, "AGL is outside the Safeguard data and Origin is mostly outside it, so neither is shown.")
    fig.savefig(FIG / "fig3_credit_use.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return p


def santos_sensitivity(corp):
    """Santos Scope 1 with and without the Curtis Island GLNG plant, in every year.

    From 2023-24 the plant is reported by GLNG Operations Pty Ltd (30% owned), so the
    two treatments give different trends. Facility-level covered emissions for the
    plant (Safeguard data) are used as a proxy for its NGER Scope 1.
    """
    fac = pd.read_csv(PROC / "facility_panel.csv")
    glng = fac[(fac.company == "Santos") & fac.facility.str.contains("GLNG", case=False)].groupby("year").covered.sum()
    incl = corp[corp.company == "Santos"].set_index("year").scope1_t
    excl = incl - glng.reindex(incl.index).fillna(0)
    out = pd.DataFrame({"incl_glng_mt": incl / 1e6, "excl_glng_mt": excl / 1e6}).round(2)
    out.to_csv(FIG / "santos_sensitivity.csv")
    for base in ("2017-18", "2020-21"):
        print(f"Santos {base} -> 2024-25: incl GLNG {incl['2024-25'] / incl[base] - 1:+.0%}, "
              f"excl GLNG {excl['2024-25'] / excl[base] - 1:+.0%}")
    return out


def main():
    FIG.mkdir(exist_ok=True)
    corp = pd.read_csv(PROC / "corporate_panel.csv")
    sg = pd.read_csv(PROC / "company_safeguard.csv")

    idx = chart1_index(corp)
    ratio = chart2_baseline(sg)
    credits = chart3_credits(sg)
    santos_sensitivity(corp)

    # The table behind the charts, for the README and for readers who want numbers.
    t1 = (corp.pivot(index="year", columns="company", values="scope1_t") / 1e6).round(2)
    t1.to_csv(FIG / "summary_table.csv")
    print("Index (2017-18 = 100), last year:\n", idx.iloc[-1].round(0).to_string())
    print("\nCovered / baseline (%):\n", ratio[["company", "year", "ratio"]].round(0).to_string(index=False))
    print("\nCredits % of covered:\n", credits.round(1).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
