# Astrolytics — NASA Space Fire Safety Explorer

**A new interactive NASA PSI combustion dashboard**, built for the NASA Space Apps Challenge 2026 / *Flame in Freefall*. It is a research exploration tool, **not** a flight-safety certification system.

## Open the dashboard

1. Download the complete `Astrolytics-Dashboard.zip` and unzip it.
2. Open **`index.html`** in Safari, Chrome, Firefox or Edge. All charts use the bundled Plotly library, and the scientific data is bundled locally, so no server, login, or API key is necessary. Custom web fonts may fall back to system fonts when offline.
3. Use the left navigation to explore the **seven views**: Overview, Fire Map, Combustion Analytics, Habitat Explorer, Research Library, Evidence Gaps, and Sources & Methods.

### Publish on GitHub Pages

1. Create a **public GitHub repository** (for example, `astrolytics-dashboard`).
2. Upload the *contents of this folder* to the repository root. Keep `index.html`, `assets/`, `data/`, `build_data.py` and `README.md` in their same relative locations.
3. Open your repository **Settings → Pages** and set **Deploy from a branch → main → / (root)**, then Save.
4. The site appears at `https://YOUR-USERNAME.github.io/astrolytics-dashboard/` after GitHub Pages deployment completes.

No Power BI license is required, and this static site is compatible with Macs, tablets and phones.

## What's included

- **19 interactive chart areas**, including the Fire Map, experimental coverage heatmap, FLEX outcome comparisons, CFI-G ignition comparisons, habitat atmospheres, research coverage and airflow evidence.
- Multiple Fire Map filters for investigation, fuel, endpoint, oxygen and pressure.
- Click-through experimental evidence inspection with PSI ID, record identifier and source-row provenance.
- A custom habitat oxygen/pressure/gravity selector with a **nearest-test search, not a safety prediction**.
- All **24 documented investigations** listed, with a transparent discoverability heuristic and original NASA PSI references.
- Normalized CSV exports and a JSON quality audit.
- Fully client-side scripts; no fabricated backend or AI model.

## Source data and key counts

The user-provided archive contains **22 CSV files from 20 PSI investigation IDs**. Four more modeled/ground-study investigations appear in the team's research guide but have no experimental CSV in the uploaded archive.

| Evidence source | Rows included | Notes |
|---|---:|---|
| FLEX / PSI-69 | 274 | 273 have valid oxygen/pressure coordinates; original outcomes preserved |
| CFI-G normal / PSI-159 | 179 | Hot ignition yes/no, ambient/test atmosphere oxygen |
| CFI-G inverse / PSI-159 | 154 | **Separate burner-stream oxygen**; excluded from ambient Fire Map |
| Flame Design / PSI-10 | 327 raw | Condition tables, **no outcomes**; only parseable numeric rows in normalized exports |
| SPICE / PSI-107 | 469 raw | Airflow measurements, **not extinction outcomes** |
| Other PSI files | Heterogeneous | Different units of observation (burns, days, samples, logs, citations) |

The archive has **861 blank padding rows** in the CFI-G inverse file, excluded from charts. An original FLEX row with pressure 0 mmHg is excluded from the oxygen/pressure plot but retained in the source/test count and quality report. Invalid negative SPICE flow entries are likewise excluded from its airflow plot with audit entries.

**Main Fire Map: 452 data points** (273 FLEX + 179 normal CFI-G). The chart also includes two atmosphere reference markers and a partial-pressure reference line; those are **not experimental measurements**.

## Scientific methods

- FLEX pressure: `psi = mmHg × (14.6959488 / 760)`.
- CFI-G pressure: `psi = bar × 14.5037738`.
- Flame Design pressure: `psi = atm × 14.6959488`.
- Oxygen mole fraction: `% = 100 × fraction`.
- CFI-G inverse `XO2` **does not represent room air** and must not be interpreted as directly equivalent to ambient tests.
- Experimental outcome labels are not standardized across investigations; never pool FLEX extinction and CFI-G ignition as a single success/failure metric.
- CFI-G termination labels `SE` and `FT` have distinct scientific meaning. Flow-terminated burn times are not natural extinction times.
- Earth vs microgravity gives evidence bounds; no direct lunar/Martian partial-gravity values are present here.
- The habitat proximity rule, `±5 oxygen percentage points and ±3 psi`, is an **exploration filter**, not a model or engineering tolerance. A normalized nearest-neighbor ranking is shown for discovery, not scientific extrapolation.
- Research discovery scores: `2 × relevance (1..3) + 2 (material evidence) + 2 (outcome-ready oxygen/pressure dataset)`. This is an editorial navigation heuristic derived from the research guide, **not** a fire-safety score.

## Rebuild the data

The `source/` folder includes the original CSV ZIP used to generate this project. From inside this repository, run:

```bash
python3 build_data.py "source/CSVs for the PSIs(1).zip"
```

The script uses the **Python standard library only** and generates:

- `data/astrolytics-data.js` — local browser dataset (no fetch needed).
- `data/astrolytics.json` — normalized data, metadata and audit log.
- `data/flex.csv`, `cfigNormal.csv`, `cfigInverse.csv`, `flameNormal.csv`, `flameInverse.csv`, `spice.csv`, `saffire.csv` — topic-specific exports.
- `data/quality-report.json` — cleaning issues and assumptions.

Every normalized experimental record includes source PSI ID and source row number.

## Limitations and validation status

This is a working chart-based application with reproducible data transformations. It does **not** contain a real LLM, online AI interpretation service or trained predictive model, and it does **not** claim direct human verification against original NASA CSV records. The original files were user-supplied; data values should be spot-checked against the official PSI pages before final scientific publication. Refer to the original [NASA PSI portal](https://psi.nasa.gov/) and the source links for each PSI ID.

The project team contributed the reference *Astrolytics — PSI Combustion Data Guide* and the *Astrolytics — Judging Criteria Review*. A judging rubric is a proposal rather than evidence of actual NASA program endorsement.

© Astrolytics contributors. Public NASA experimental data remain attributed to their original NASA PSI investigations.
