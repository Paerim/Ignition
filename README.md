# HUB 4x4 Quality Dashboard (Ignition Perspective)

Ignition 8.1 project with a Perspective version of the HUB 4x4 quality dashboard.

## Contents

| Path | What |
|---|---|
| `com.inductiveautomation.perspective/views/HUB4x4/QualityDashboard` | Main dashboard (page `/`) |
| `.../views/HUB4x4/Components/*` | Reusable views: KpiTile, BarRow, LineStatusRow, AbnormalItem |
| `.../views/HUB4x4/Popups/AbnormalDetail` | "More detail" popup |
| `ignition/script-python/hub4x4/data` | Data provider (`hub4x4.data.getDashboard`) |
| `db/hub4x4_schema.sql` | Tables used when reading from a database |
| `assets/layout/` | Line layout picture and per-point highlight overlays (embedded into the view) |
| `tools/make_layout_assets.py` | Rebuilds the overlays from `line_layout_source.png` (needs Pillow, numpy, scipy) |
| `tools/build_views.py` | Generator for the view JSON. Edit layout here, then run `python3 tools/build_views.py` |

## Dashboard sections

- KPI: Total Plan, FG, OK, NG, PPM, Repair status (Total / Closed / On Process)
- Period buttons Hourly / Daily / Weekly / Monthly + date range (from / to)
- Inspection Item Point A-F: click to switch the control chart (UCL / LCL / Target, warning points in orange)
- Line Layout: picture of the line; the stations of the selected Inspection Item are highlighted
  (A: 110A/110B, B: 120A/120B, C: 130A/130B/130C, D: 140A/140B/140C, E: 125A/125B, F: Q)
- Production Line: performance % with green (>=97) / orange (>=90) / red dot
- Total NG tendency, OP Performance, Top 5 Defects, Repair cause
- Abnormal List (NG + Repair) with a "More detail" popup

Data refreshes every 10 seconds (`now(10000)` in the `view.custom.data` binding).

## Install

1. Copy this folder to `<Ignition>/data/projects/<ProjectName>/` (or zip it and use Gateway → Projects → Import).
2. Gateway scans projects automatically; or open the project in the Designer.
3. Open `http://<gateway>:8088/data/perspective/client/<ProjectName>/`.

## Simulated data → real database

The dashboard runs on simulated data by default. To use a database:

1. Create the tables in `db/hub4x4_schema.sql` and feed them from your PLC/MES (Transaction Groups, gateway scripts, etc.).
2. In `hub4x4/data` set `USE_DB = True` and `DB = "<your DB connection name>"`.

Control-chart limits per point live in `LIMITS` in the same script (the DB version reads them from `hub_inspection`).
PPM is calculated as `NG / FG x 1,000,000`.

## Changing the line layout picture

1. Replace `assets/layout/line_layout_source.png`.
2. Update the station centres in `STATIONS` and the point mapping in `POINTS` (`tools/make_layout_assets.py`),
   and `POINT_STATIONS` in `tools/build_views.py`.
3. Run `python3 tools/make_layout_assets.py` then `python3 tools/build_views.py`.
