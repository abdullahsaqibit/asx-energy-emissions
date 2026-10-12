# Which ASX energy producers are really cutting emissions?

A comparison of five ASX-listed energy producers (AGL, Beach Energy, Origin, Santos and Woodside) using nine years of Clean Energy Regulator data, 2016-17 to 2024-25.

**Short answer.** On reported Scope 1 emissions, Santos (−49%) and AGL (−29%) cut the most between 2017-18 and 2024-25, Woodside (−18%) and Origin (−13%) cut less, and Beach rose (+10%). The data cannot show how much of each fall is a *real* cut. Part of Santos's fall is carbon capture and storage, and none of the figures is adjusted for production, acquisitions or asset sales. Those limits are set out below, and they matter more than the ranking.

![Scope 1 emissions indexed to 2017-18](figures/fig1_scope1_index.png)

## Data

All from the [Clean Energy Regulator](https://cer.gov.au) (files in `data/raw/cer/`):

- **NGER corporate emissions**, 2016-17 to 2024-25: Scope 1 and 2 emissions by controlling corporation, Australian operations, July to June years.
- **Safeguard Mechanism facility data**, 2016-17 to 2024-25: covered emissions, baselines, and carbon credits surrendered, by facility. The regulator changed the table layout in 2023-24, when the reformed baselines began, so the code harmonises two layouts.
- **Company reports** (annual and climate reports from Woodside, Santos, Origin, AGL and Beach) were used to check the Santos figures. The PDFs are not included in this repository because of their size; they are public on each company's website.

## Method

1. `src/01_corporate_panel.py` builds a company-by-year table from the NGER files.
2. `src/02_safeguard_panel.py` builds a facility-by-year table from the Safeguard files and sums it to company level.
3. `src/03_charts.py` draws the three figures and writes the summary table.

## Results

Scope 1 emissions, Mt CO2-e (NGER):

| Year | AGL | Beach | Origin | Santos | Woodside |
|---|---|---|---|---|---|
| 2016-17 | 43.44 | – | 17.16 | 5.70 | 10.16 |
| 2017-18 | 43.10 | 0.50 | 18.15 | 5.39 | 9.97 |
| 2018-19 | 42.73 | 0.44 | 17.96 | 5.82 | 9.22 |
| 2019-20 | 42.23 | 0.47 | 16.00 | 7.32 | 9.19 |
| 2020-21 | 40.21 | 0.41 | 14.88 | 7.49 | 9.08 |
| 2021-22 | 39.51 | 0.44 | 12.84 | 7.28 | 8.99 |
| 2022-23 | 34.80 | 0.44 | 13.68 | 6.47 | 9.27 |
| 2023-24 | 32.91 | 0.45 | 15.56 | 4.23 | 8.42 |
| 2024-25 | 30.44 | 0.54 | 15.80 | 2.77 | 8.18 |
| **Change since 2017-18** | **−29%** | **+10%** | **−13%** | **−49%** | **−18%** |

- **AGL** fell steadily every year.
- **Santos** rose to a peak in 2020-21 (7.49 Mt), then fell by 63% to 2024-25.
- **Origin** reached a low in 2021-22 (12.84 Mt) and has risen each year since.
- **Beach** is small (about 0.5 Mt) and has no 2016-17 row in the NGER file.

### After the 2023 Safeguard reform

![Covered emissions as a share of Safeguard baselines](figures/fig2_vs_baseline.png)

Summed across their facilities, Woodside and Beach were above their baselines in both 2023-24 and 2024-25. Santos fell from 104% to 72%.

![Carbon credit use](figures/fig3_credit_use.png)

Credits surrendered as a share of covered emissions: no credits were surrendered before 2022-23. Since then Woodside's share has risen each year (0% → 8% → 14%). Santos (0% → 10% → 6%) and Beach (14% → 25% → 8%) rose and then fell.

## Limitations

- **No production adjustment.** A company that produces less will look like it is "cutting". Intensity (emissions per unit of output) would be a fairer test and is the main next step. The company reports in `data/raw/reports/` are the likely source.
- **Acquisitions and asset sales are not adjusted.** Reported totals move when companies buy or sell assets, not only when they cut emissions.
- **Santos and carbon capture.** Santos's own 2025 annual report states that its emissions are reported after CO2 captured and stored by its Moomba CCS project (1.23 Mt stored in 2025). The three sources I compared all show Santos falling (NGER 7.49 → 2.77 Mt from 2020-21 to 2024-25, Safeguard covered emissions 6.74 → 2.19 Mt, and Santos's own global operated Scope 1, 6.40 → 3.61 Mt from 2021 to 2025), so the direction is not a data artefact. I have not checked whether the regulator's figures net off captured CO2 in the same way as the company report.
- **Year definitions differ.** NGER years run July to June. Santos's report appears to use calendar years (not confirmed).
- **Scope of the regulator's data.** NGER covers Australian operations only, so global emissions (for example Santos in PNG) are not included.
- **Safeguard coverage is partial.** AGL does not appear in the Safeguard facility tables. The only power stations listed are off-grid ones, and I believe grid-connected generators are outside the scheme, but I have not confirmed that. Only about 4% of Origin's NGER emissions are in Safeguard facilities.
- **Net totals.** In the pre-2023 layout, facilities on multi-year monitoring periods report "n/a" for baseline and net emissions. Company totals for those are left blank, not summed with missing values.
- **Company-level baseline ratio.** Figure 2 sums baselines and covered emissions across a company's facilities. The legal obligation applies facility by facility, so a company can be under its total baseline and still owe credits at some facilities.
- **Names.** Woodside Petroleum became Woodside Energy Group in 2021-22 and is treated as one company. Responsible-emitter names in the Safeguard files include subsidiaries (for example Woodside Burrup, Origin Energy Upstream Operator).
- **Beach** has no NGER row for 2016-17, so all indexed charts start in 2017-18.

## Reproduce

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/01_corporate_panel.py
python src/02_safeguard_panel.py
python src/03_charts.py
```

Outputs: `data/processed/` (panels) and `figures/` (charts and `summary_table.csv`).
