#!/usr/bin/env python3
"""
Generates the Perspective views for the HUB 4x4 Quality Dashboard.

    python3 tools/build_views.py

Writes into com.inductiveautomation.perspective/views/HUB4x4/... and the page config.
Edit layout/colours here and re-run, rather than hand-editing the view.json files.
"""
import base64
import json
import os
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PERSP = os.path.join(ROOT, "com.inductiveautomation.perspective")
TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ------------------------------------------------------------------ palette
BG = "#1B5E75"
HEADER = "#0E3F52"
TILE = "#FFFFFF"
INK = "#1F2D3D"
MUTED = "#5B6B7A"
BTN = "#A9C4EB"
BTN_ON = "#2E6DB4"
DARK = "#0D1B2A"
DARK_INK = "#C9D6E3"
BLUE = "#1F6FA8"
CYAN = "#3AB6E8"
ORANGE = "#F28C28"
YELLOW = "#E8C547"
PURPLE = "#8E2BA8"
ABN_BG = "#CFEFFB"

DESIGN_W, DESIGN_H = 1600, 900
LAYOUT_DIR = os.path.join(ROOT, "assets", "layout")   # made by tools/make_layout_assets.py

# Inspection point -> stations highlighted on the line layout
POINT_STATIONS = {
    "A": "110A / 110B",
    "B": "120A / 120B",
    "C": "130A / 130B / 130C",
    "D": "140A / 140B / 140C",
    "E": "125A / 125B",
    "F": "Q",
}


def data_uri(png):
    with open(os.path.join(LAYOUT_DIR, png), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


# ------------------------------------------------------------------ helpers
def P(x, y, w, h, W=DESIGN_W, H=DESIGN_H):
    """Pixel rect in a W x H design -> percent-mode coordinate position."""
    return {"x": round(x / W, 5), "y": round(y / H, 5),
            "width": round(w / W, 5), "height": round(h / H, 5)}


def F(basis="auto", grow=0, shrink=0):
    return {"basis": basis, "grow": grow, "shrink": shrink}


def comp(type_, name, props=None, position=None, propConfig=None, events=None,
         children=None, custom=None):
    c = {"type": type_, "version": 0, "meta": {"name": name}, "props": props or {}}
    if position is not None:
        c["position"] = position
    if propConfig:
        c["propConfig"] = propConfig
    if events:
        c["events"] = events
    if children is not None:
        c["children"] = children
    if custom:
        c["custom"] = custom
    return c


def prop(path, transforms=None, bidirectional=False):
    b = {"type": "property", "config": {"path": path}}
    if bidirectional:
        b["config"]["bidirectional"] = True
    if transforms:
        b["transforms"] = transforms
    return {"binding": b}


def expr(expression, transforms=None):
    b = {"type": "expr", "config": {"expression": expression}}
    if transforms:
        b["transforms"] = transforms
    return {"binding": b}


def fmt(pattern):
    return [{"type": "format", "formatType": "numeric", "formatValue": pattern}]


def script(body):
    return {"config": {"script": "\n".join("\t" + l for l in body.strip("\n").split("\n"))},
            "scope": "G", "type": "script"}


def label(name, text="", style=None, position=None, propConfig=None, events=None, **props):
    p = {"text": text, "style": style or {}}
    p.update(props)
    return comp("ia.display.label", name, p, position, propConfig, events)


def flex(name, children, direction="row", style=None, position=None, propConfig=None, **props):
    p = {"direction": direction, "style": style or {}}
    p.update(props)
    return comp("ia.container.flex", name, p, position, propConfig, children=children)


def tile_style(**extra):
    s = {"backgroundColor": TILE, "borderRadius": "4px", "boxShadow": "0 1px 3px rgba(0,0,0,0.35)",
         "overflow": "hidden"}
    s.update(extra)
    return s


def write_view(path, view):
    d = os.path.join(PERSP, "views", *path.split("/"))
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "view.json"), "w") as f:
        json.dump(view, f, indent=2)
    write_resource(d, "view.json")


def write_resource(d, filename):
    res = {"scope": "G", "version": 1, "restricted": False, "overridable": True,
           "files": [filename],
           "attributes": {"lastModification": {"actor": "admin", "timestamp": TS}}}
    with open(os.path.join(d, "resource.json"), "w") as f:
        json.dump(res, f, indent=2)


def view(root, defaultSize, params=None, custom=None, propConfig=None, events=None):
    v = {"custom": custom or {}, "params": params or {}, "props": {"defaultSize": defaultSize},
         "root": root}
    pc = dict(propConfig or {})
    for k in (params or {}):
        pc.setdefault("params." + k, {"paramDirection": "input", "persistent": True})
    if pc:
        v["propConfig"] = pc
    if events:
        v["events"] = events
    return v


# ------------------------------------------------------------------ XY chart pieces
def axis(name, render, color, title="", fmt_="#,##0.##", min_="", max_="", grid=True):
    return {
        "name": name,
        "label": {"enabled": bool(title), "text": title, "color": color},
        "visible": True,
        "tooltip": {"enabled": False, "text": "", "cornerRadius": 3, "pointerLength": 4,
                    "inPercent": False, "background": {"color": "", "opacity": 1}},
        "render": render,
        "category": {"break": {"enabled": False, "startCategory": "", "endCategory": "", "breakSize": 0.01}},
        "date": {"baseInterval": {"enabled": False, "timeUnit": "second", "count": 1, "skipEmptyPeriods": False},
                 "range": {"max": "", "min": "", "useStrict": False},
                 "inputFormat": "yyyy-MM-dd kk:mm:ss", "format": "M/d"},
        "value": {"range": {"max": max_, "min": min_, "useStrict": max_ != "" or min_ != ""},
                  "logarithmic": False, "format": fmt_,
                  "break": {"enabled": False, "startValue": 0, "endValue": 100, "breakSize": 0.01}},
        "inversed": False,
        "appearance": {
            "opposite": False, "inside": False,
            "labels": {"color": color, "opacity": 1},
            "grid": {"color": color, "opacity": 0.15 if grid else 0, "dashArray": "",
                     "minDistance": None, "position": 0.5},
            "font": {"size": "11px", "weight": 400},
        },
    }


def series(name, text, source, x, y, render, color, stroke_w=2, dash="", bullets=True,
           bullet_color=None, line_opacity=1, tooltip=True, legend=True):
    bullet = {
        "enabled": bullets, "render": "circle", "width": 8, "height": 8,
        "label": {"text": "", "position": {"dx": 0, "dy": 0}},
        "tooltip": {"enabled": tooltip, "text": "{name}: [bold]{valueY}[/]", "cornerRadius": 3,
                    "pointerLength": 4, "background": {"color": "", "opacity": 1}},
        "fill": {"color": bullet_color or color, "opacity": 1},
        "stroke": {"color": bullet_color or color, "width": 1, "opacity": 1},
        "rotation": 0,
        "anchor": {"horizontal": "center", "vertical": "middle"},
        "deriveFieldsFromData": {"fill": {"color": "", "opacity": ""}, "stroke": {"color": "", "opacity": "", "width": ""},
                                 "rotation": ""},
        "heatRules": {"enabled": False, "max": 100, "min": 2, "dataField": ""},
    }
    return {
        "name": name,
        "label": {"text": text},
        "visible": True,
        "hiddenInLegend": not legend,
        "defaultState": {"visible": True},
        "data": {"source": source, "x": x, "y": y},
        "xAxis": "x",
        "yAxis": "y",
        "zIndex": 0,
        "tooltip": {"enabled": tooltip, "text": "{name}: [bold]{valueY}[/]", "cornerRadius": 3,
                    "pointerLength": 4, "background": {"color": "", "opacity": 1}},
        "render": render,
        "candlestick": {"open": {"x": "", "y": ""}, "high": {"x": "", "y": ""}, "low": {"x": "", "y": ""},
                        "appearance": {"fill": {"color": "", "opacity": 1}, "stroke": {"color": "", "opacity": 1, "width": 1},
                                       "stacked": False, "deriveFieldsFromData": {"fill": {"color": "", "opacity": ""},
                                                                                  "stroke": {"color": "", "opacity": "", "width": ""}},
                                       "heatRules": {"enabled": False, "max": "", "min": "", "dataField": ""}}},
        "column": {"open": {"x": "", "y": ""},
                   "appearance": {"fill": {"color": color, "opacity": 1},
                                  "stroke": {"color": color, "opacity": 1, "width": 1},
                                  "stacked": False, "width": 0.55, "height": None,
                                  "cornerRadius": {"topLeft": 0, "topRight": 0, "bottomLeft": 0, "bottomRight": 0},
                                  "deriveFieldsFromData": {"fill": {"color": "", "opacity": ""},
                                                           "stroke": {"color": "", "opacity": "", "width": ""}},
                                  "heatRules": {"enabled": False, "max": "", "min": "", "dataField": ""}}},
        "line": {"open": {"x": "", "y": ""},
                 "appearance": {"connect": True, "tensionX": 1, "tensionY": 1, "minDistance": 0.5,
                                "stroke": {"width": stroke_w, "opacity": line_opacity, "color": color, "dashArray": dash},
                                "fill": {"opacity": 0, "color": color},
                                "bullets": [bullet]}},
        "stepLine": {"open": {"x": "", "y": ""},
                     "appearance": {"connect": True, "tensionX": 1, "tensionY": 1, "minDistance": 0.5,
                                    "stroke": {"width": 3, "opacity": 1, "color": "", "dashArray": ""},
                                    "fill": {"opacity": 0, "color": ""}, "bullets": []}},
    }


def xy_chart(name, position, source_path, source, xaxis, yaxis, series_list, bg="transparent",
             legend=False):
    return comp("ia.chart.xy", name, {
        "dataSources": {source: []},
        "xAxes": [xaxis],
        "yAxes": [yaxis],
        "series": series_list,
        "legend": {"enabled": legend, "position": "bottom"},
        "cursor": {"enabled": False, "lineX": {"enabled": True}, "lineY": {"enabled": False}},
        "style": {"backgroundColor": bg},
    }, position, {"props.dataSources." + source: prop(source_path)})


def chart_card(name, title, position, chart, dark=False):
    s = tile_style() if not dark else {"backgroundColor": DARK, "borderRadius": "4px",
                                        "border": "2px solid " + ORANGE}
    return flex(name, [
        label("Title", title, {"color": DARK_INK if dark else MUTED, "fontSize": "13px",
                                "textAlign": "center", "paddingTop": "4px"}, F("22px")),
        chart,
    ], "column", s, position)


# ================================================================== sub views
def build_kpi_tile():
    root = flex("root", [
        label("Title", "", {"color": INK, "fontSize": "18px", "textAlign": "center"}, F("auto", 1, 1),
              {"props.text": prop("view.params.title")}),
        label("Value", "", {"color": INK, "fontSize": "24px", "fontWeight": "bold", "textAlign": "center"},
              F("auto", 1, 1), {"props.text": prop("view.params.value")}),
    ], "column", tile_style(justifyContent="center"))
    return view(root, {"width": 140, "height": 95}, {"title": "FG", "value": "0"})


def build_bar_row():
    root = flex("root", [
        label("Name", "", {"color": INK, "fontSize": "12px", "textAlign": "right",
                           "paddingRight": "8px", "whiteSpace": "nowrap"}, F("110px"),
              {"props.text": prop("view.params.name")}),
        comp("ia.display.progress", "Bar", {
            "value": 0, "min": 0, "max": 100,
            "bar": {"color": BLUE},
            "track": {"color": "#E6EDF3"},
            "valueDisplay": {"enabled": False},
            "style": {"height": "16px"},
        }, F("auto", 1, 1), {
            "props.value": prop("view.params.value"),
            "props.max": prop("view.params.max"),
        }),
        label("Text", "", {"color": INK, "fontSize": "12px", "textAlign": "right", "paddingRight": "6px"},
              F("56px"), {"props.text": prop("view.params.text")}),
    ], "row", {"alignItems": "center"})
    return view(root, {"width": 400, "height": 26},
                {"name": "Scratch", "value": 20, "max": 100, "text": "20%"})


def build_line_row():
    root = flex("root", [
        label("Line", "", {"color": INK, "fontSize": "17px", "paddingLeft": "8px"}, F("auto", 1, 1),
              {"props.text": prop("view.params.line")}),
        label("Perf", "", {"color": INK, "fontSize": "17px", "textAlign": "right"}, F("60px"),
              {"props.text": expr("concat(toStr({view.params.perf}), '%')")}),
        flex("DotWrap", [
            flex("Dot", [], "row", {"width": "12px", "height": "12px", "borderRadius": "50%"},
                 F("12px"), {"props.style.backgroundColor": prop("view.params.color")}),
        ], "row", {"justifyContent": "center", "alignItems": "center"}, F("44px")),
    ], "row", {"alignItems": "center"})
    return view(root, {"width": 220, "height": 30},
                {"line": "110A", "perf": 98, "color": "#2DB84B"})


def build_abnormal_item():
    md = ("concat('**', {view.params.ts}, '** Seq.', {view.params.seq}, "
          "'  \\n**Detail :** point ', {view.params.point}, ' (', {view.params.result}, ') - ', "
          "{view.params.detail}, '  \\n**Process:** ', {view.params.process})")
    open_popup = script("""
system.perspective.openPopup('abnormalDetail', 'HUB4x4/Popups/AbnormalDetail',
	params={'ts': self.view.params.ts, 'seq': self.view.params.seq, 'line': self.view.params.line,
	        'point': self.view.params.point, 'result': self.view.params.result,
	        'process': self.view.params.process, 'detail': self.view.params.detail},
	title='Abnormal Detail', modal=True, showCloseIcon=True, draggable=True,
	position={'width': 420, 'height': 320})
""")
    root = flex("root", [
        comp("ia.display.markdown", "Text", {
            "source": "", "markdown": {"escapeHtml": True},
            "style": {"color": INK, "fontSize": "13px", "lineHeight": "1.35"},
        }, F("auto", 1, 1), {"props.source": expr(md)}),
        label("More", "More detail", {"color": "#1565C0", "textDecoration": "underline",
                                      "cursor": "pointer", "fontSize": "13px"}, F("18px"),
              events={"dom": {"onClick": open_popup}}),
    ], "column", {"borderBottom": "1px solid #9FC9DA", "padding": "6px 8px"})
    root["propConfig"] = {"props.style.borderLeft": expr(
        "if({view.params.result} = 'NG', '4px solid #E53935', '4px solid " + ORANGE + "')")}
    return view(root, {"width": 480, "height": 84},
                {"ts": "", "seq": "", "line": "", "point": "", "result": "", "process": "", "detail": ""})


def build_abnormal_popup():
    rows = []
    for key, title in [("ts", "Date/Time"), ("seq", "Seq."), ("line", "Line"), ("point", "Inspection point"),
                       ("result", "Result"), ("process", "Process"), ("detail", "Defect")]:
        rows.append(flex("Row_" + key, [
            label("K", title, {"color": MUTED, "fontSize": "14px"}, F("140px")),
            label("V", "", {"color": INK, "fontSize": "14px", "fontWeight": "bold"}, F("auto", 1, 1),
                  {"props.text": prop("view.params." + key)}),
        ], "row", {"borderBottom": "1px solid #E3E8EE"}, F("32px")))
    rows.append(flex("Actions", [
        comp("ia.input.button", "Close", {"text": "Close", "style": {"backgroundColor": BTN_ON}},
             F("100px"), events={"component": {"onActionPerformed": script(
                 "system.perspective.closePopup('abnormalDetail')")}}),
    ], "row", {"justifyContent": "flex-end", "marginTop": "10px"}, F("36px")))
    root = flex("root", rows, "column", {"padding": "12px", "backgroundColor": TILE})
    return view(root, {"width": 420, "height": 320},
                {"ts": "", "seq": "", "line": "", "point": "", "result": "", "process": "", "detail": ""})


# ================================================================== main view
def build_dashboard():
    D = "view.custom.data."
    ch = []

    # ---- header
    ch.append(flex("Header", [], "row", {"backgroundColor": HEADER}, P(0, 0, 1600, 62)))
    ch.append(label("Title", "HUB 4x4 Quality Dashboard",
                    {"color": "#FFFFFF", "fontSize": "28px", "fontWeight": "bold", "textAlign": "center"},
                    P(450, 6, 700, 50)))
    ch.append(label("Updated", "", {"color": "#9CC3D3", "fontSize": "12px"}, P(20, 18, 300, 26),
                    {"props.text": expr("concat('Updated: ', {view.custom.data.updated})")}))
    date_style = {"fontSize": "14px"}
    ch.append(flex("DateRange", [
        label("L1", "Date : from", {"color": "#FFFFFF", "fontSize": "15px", "whiteSpace": "nowrap"}, F("86px")),
        comp("ia.input.date-time-input", "From", {"pickerType": "date", "format": "DD/MM/YY",
                                                  "style": date_style}, F("auto", 1, 1),
             {"props.value": prop("view.custom.startDate", bidirectional=True)}),
        label("L2", "to", {"color": "#FFFFFF", "fontSize": "15px", "textAlign": "center"}, F("26px")),
        comp("ia.input.date-time-input", "To", {"pickerType": "date", "format": "DD/MM/YY",
                                                "style": date_style}, F("auto", 1, 1),
             {"props.value": prop("view.custom.endDate", bidirectional=True)}),
    ], "row", {"backgroundColor": "#3E7FB8", "border": "2px solid #FFFFFF", "borderRadius": "6px",
               "alignItems": "center", "padding": "0 8px", "gap": "4px"}, P(1150, 9, 430, 44)))

    # ---- KPI tiles
    for i, (nm, title, path, pattern, x, w) in enumerate([
        ("KpiPlan", "Total Plan", "kpi.plan", "#,##0", 20, 175),
        ("KpiFG", "FG", "kpi.fg", "#,##0", 210, 125),
        ("KpiOK", "OK", "kpi.ok", "#,##0", 345, 125),
        ("KpiNG", "NG", "kpi.ng", "#,##0", 480, 125),
        ("KpiPPM", "PPM", "kpi.ppm", "#,##0", 615, 125),
    ]):
        ch.append(comp("ia.display.view", nm, {
            "path": "HUB4x4/Components/KpiTile", "params": {"title": title, "value": ""},
            "useDefaultViewWidth": False, "useDefaultViewHeight": False,
        }, P(x, 76, w, 95), {"props.params.value": prop(D + path, fmt(pattern))}))

    def repair_col(name, title, path):
        return flex(name, [
            label("T", title, {"color": INK, "fontSize": "17px", "textAlign": "center"}, F("auto", 1, 1)),
            label("V", "", {"color": INK, "fontSize": "20px", "fontWeight": "bold", "textAlign": "center"},
                  F("auto", 1, 1), {"props.text": prop(D + path)}),
        ], "column", {}, F("auto", 1, 1))

    ch.append(flex("RepairStatus", [
        label("Title", "Repair status", {"color": INK, "fontSize": "18px", "textAlign": "center"}, F("26px")),
        flex("Cols", [repair_col("Total", "Total", "repair.total"),
                      repair_col("Closed", "Closed", "repair.closed"),
                      repair_col("OnProcess", "On Process", "repair.onProcess")],
             "row", {}, F("auto", 1, 1)),
    ], "column", tile_style(padding="4px"), P(755, 76, 470, 95)))

    # ---- period buttons
    for nm, x, y in [("Hourly", 1240, 72), ("Daily", 1412, 72), ("Weekly", 1240, 124), ("Monthly", 1412, 124)]:
        ch.append(comp("ia.input.button", "Btn" + nm, {
            "text": nm,
            "style": {"fontSize": "18px", "borderRadius": "6px", "border": "none", "color": "#FFFFFF"},
        }, P(x, y, 168, 46), {
            "props.style.backgroundColor": expr("if({view.custom.period} = '%s', '%s', '%s')" % (nm, BTN_ON, BTN)),
        }, {"component": {"onActionPerformed": script("hub4x4.data.applyPeriod(self.view, '%s')" % nm)}}))

    # ---- inspection items
    items = [label("Head", "Inspection Item", {"color": INK, "fontSize": "17px", "fontWeight": "bold",
                                               "textAlign": "center"}, F("52px"))]
    for p in "ABCDEF":
        items.append(label("Point" + p, "Point " + p,
                           {"fontSize": "17px", "textAlign": "center", "cursor": "pointer", "borderRadius": "4px",
                            "margin": "1px 10px"}, F("auto", 1, 1), {
                               "props.style.backgroundColor": expr(
                                   "if({view.custom.selectedPoint} = '%s', '%s', 'transparent')" % (p, BTN_ON)),
                               "props.style.color": expr(
                                   "if({view.custom.selectedPoint} = '%s', '#FFFFFF', '%s')" % (p, INK)),
                           }, {"dom": {"onClick": script("self.view.custom.selectedPoint = '%s'" % p)}}))
    ch.append(flex("InspectionItems", items, "column", tile_style(paddingBottom="8px"), P(20, 186, 175, 345)))

    # ---- control chart
    cc_src = "view.custom.data.controlChart.points"
    control = xy_chart("ControlChart", F("auto", 1, 1), cc_src, "points",
                       axis("x", "category", DARK_INK, grid=False),
                       axis("y", "value", DARK_INK, fmt_="#,##0.00"),
                       [series("ucl", "UCL", "points", "seq", "ucl", "line", YELLOW, 1.5, "6,4", False, tooltip=False),
                        series("lcl", "LCL", "points", "seq", "lcl", "line", YELLOW, 1.5, "6,4", False, tooltip=False),
                        series("target", "Target", "points", "seq", "target", "line", "#6C7A89", 1, "2,4", False, tooltip=False),
                        series("value", "Value", "points", "seq", "value", "line", "#9FB3C8", 1.5, bullet_color=CYAN),
                        series("warn", "Warning", "points", "seq", "warn", "line", ORANGE, 0, bullet_color=ORANGE,
                               line_opacity=0)],
                       bg=DARK, legend=True)
    card = chart_card("ControlChartCard", "", P(205, 186, 455, 345), control, dark=True)
    card["children"][0]["propConfig"] = {"props.text": expr(
        "concat('Hub 4x4 : Point ', {view.custom.selectedPoint}, '    (LCL ', "
        "numberFormat({view.custom.data.controlChart.lcl}, '0.00'), ' / UCL ', "
        "numberFormat({view.custom.data.controlChart.ucl}, '0.00'), ')')")}
    card["children"][0]["props"]["style"].update({"fontSize": "16px", "color": "#FFFFFF"})
    ch.append(card)

    # ---- line layout: picture + highlight of the selected point's stations
    LW, LH = 660, 345
    img_pos = P(10, 42, 640, 159, LW, LH)       # keeps the 1497 x 372 picture ratio
    stations_expr = "case({view.custom.selectedPoint}, %s, '')" % ", ".join(
        "'%s', '%s'" % kv for kv in POINT_STATIONS.items())
    lay = [
        label("Title", "", {"color": INK, "fontSize": "16px", "fontWeight": "bold", "paddingLeft": "4px"},
              P(10, 6, 640, 30, LW, LH), {"props.text": expr(
                  "concat('Line Layout :  Point ', {view.custom.selectedPoint}, '  >  Station ', " + stations_expr + ")")}),
        comp("ia.display.image", "Layout", {"source": data_uri("base.png"), "fit": {"mode": "contain"},
                                            "style": {}}, img_pos),
    ]
    for p in POINT_STATIONS:
        ov = comp("ia.display.image", "Highlight" + p, {
            "source": data_uri("point_%s.png" % p), "fit": {"mode": "contain"},
            "style": {"filter": "drop-shadow(0 0 4px #FF6A00) drop-shadow(0 0 8px rgba(255,140,0,0.8))",
                      "pointerEvents": "none"},
        }, img_pos, {"meta.visible": expr("{view.custom.selectedPoint} = '%s'" % p)})
        lay.append(ov)
    chips = []
    for p, st in POINT_STATIONS.items():
        on = "{view.custom.selectedPoint} = '%s'" % p
        chips.append(flex("Chip" + p, [
            label("P", "Point " + p, {"fontSize": "14px", "fontWeight": "bold", "textAlign": "center"}, F("auto", 1, 1),
                  {"props.style.color": expr("if(%s, '#FFFFFF', '%s')" % (on, INK))}),
            label("S", st, {"fontSize": "12px", "textAlign": "center"}, F("auto", 1, 1),
                  {"props.style.color": expr("if(%s, '#FFFFFF', '%s')" % (on, MUTED))}),
        ], "column", {"borderRadius": "6px", "cursor": "pointer", "margin": "4px", "padding": "4px 2px",
                      "border": "1px solid #D5DDE5"}, F("0", 1, 1), {
            "props.style.backgroundColor": expr("if(%s, '#F28C28', '#F4F6F8')" % on),
        }))
        chips[-1]["events"] = {"dom": {"onClick": script("self.view.custom.selectedPoint = '%s'" % p)}}
    lay.append(flex("PointMap", chips, "row", {"alignItems": "stretch"}, P(10, 222, 640, 70, LW, LH)))
    lay.append(label("Hint", "Click an Inspection Item (or a point above) to highlight where it is measured on the line.",
                     {"color": MUTED, "fontSize": "12px", "paddingLeft": "8px"}, P(10, 300, 640, 30, LW, LH)))
    ch.append(comp("ia.container.coord", "LineLayout", {
        "mode": "percent", "style": tile_style(),
    }, P(670, 186, 660, 345), children=lay))

    # ---- production line
    ch.append(flex("ProductionLine", [
        label("Head", "Production Line", {"color": INK, "fontSize": "18px", "textAlign": "center",
                                          "borderBottom": "1px solid #D5DDE5"}, F("34px")),
        label("Sub", "Last status & Performance", {"color": INK, "fontSize": "14px", "paddingLeft": "8px"}, F("26px")),
        comp("ia.display.flex-repeater", "Lines", {
            "path": "HUB4x4/Components/LineStatusRow", "direction": "column", "instances": [],
            "useDefaultViewWidth": False, "useDefaultViewHeight": True,
            "elementPosition": {"basis": "auto", "grow": 0, "shrink": 0},
            "style": {"overflowY": "auto"},
        }, F("auto", 1, 1), {"props.instances": prop(D + "lines")}),
    ], "column", tile_style(), P(1340, 186, 240, 345)))

    # ---- NG tendency (line)
    ng = xy_chart("Chart", F("auto", 1, 1), D + "ngTrend", "trend",
                  axis("x", "category", MUTED, grid=False), axis("y", "value", MUTED, fmt_="#,##0", min_=0),
                  [series("ng", "NG", "trend", "bucket", "ng", "line", BLUE, 2.5)])
    ch.append(chart_card("NgTendency", "Total NG tendency", P(20, 545, 560, 168), ng))

    # ---- OP performance (column)
    op = xy_chart("Chart", F("auto", 1, 1), D + "opPerformance", "op",
                  axis("x", "category", MUTED, grid=False), axis("y", "value", MUTED, fmt_="#,##0", min_=0),
                  [series("ng", "NG", "op", "op", "ng", "column", BLUE)])
    ch.append(chart_card("OpPerformance", "OP Performance (NG by OP)", P(20, 722, 560, 168), op))

    # ---- Top 5 defects / repair cause (bar rows)
    def bars(name, title, position, source, txt_expr, max_expr):
        return flex(name, [
            label("Title", title, {"color": INK, "fontSize": "14px", "fontWeight": "bold", "padding": "4px 8px"}, F("26px")),
            comp("ia.display.flex-repeater", "Bars", {
                "path": "HUB4x4/Components/BarRow", "direction": "column", "instances": [],
                "useDefaultViewWidth": False, "useDefaultViewHeight": True,
                "elementPosition": {"basis": "auto", "grow": 0, "shrink": 0},
                "style": {"justifyContent": "space-around"},
            }, F("auto", 1, 1), {"props.instances": prop(D + source, [{
                "type": "script",
                "code": "\n".join("\t" + l for l in (
                    "out = []\n"
                    "rows = value or []\n"
                    "mx = max([%s for r in rows] or [1])\n" % max_expr +
                    "for r in rows:\n"
                    "\tout.append(%s)\n" % txt_expr +
                    "return out").split("\n")),
            }])}),
        ], "column", tile_style(), position)

    ch.append(bars("TopDefects", "Top 5 Defects", P(590, 545, 480, 168), "topDefects",
                   "{'name': r['name'], 'value': r['pct'], 'max': 100, 'text': '%s%%' % r['pct']}", "r['pct']"))
    ch.append(bars("RepairCause", "Repair cause", P(590, 722, 480, 168), "repairCause",
                   "{'name': r['name'], 'value': r['value'], 'max': mx, 'text': str(r['value'])}", "r['value']"))

    # ---- abnormal list
    ch.append(flex("AbnormalList", [
        flex("HeadWrap", [
            label("Head", "Abnormal List ( NG + Repair )", {"color": "#FFFFFF", "fontSize": "20px", "textAlign": "center",
                               "backgroundImage": "linear-gradient(#B24AC9, %s)" % PURPLE,
                               "borderRadius": "4px", "boxShadow": "0 2px 4px rgba(0,0,0,0.35)"},
                  F("auto", 1, 1)),
        ], "row", {"padding": "8px"}, F("56px")),
        comp("ia.display.flex-repeater", "Items", {
            "path": "HUB4x4/Components/AbnormalItem", "direction": "column", "instances": [],
            "useDefaultViewWidth": False, "useDefaultViewHeight": True,
            "elementPosition": {"basis": "auto", "grow": 0, "shrink": 0},
            "style": {"overflowY": "auto"},
        }, F("auto", 1, 1), {"props.instances": prop(D + "abnormal")}),
    ], "column", {"backgroundColor": ABN_BG, "borderRadius": "4px"}, P(1080, 545, 500, 345)))

    root = comp("ia.container.coord", "root", {
        "mode": "percent",
        "style": {"backgroundColor": BG, "border": "4px solid " + HEADER, "fontFamily": "Segoe UI, Arial, sans-serif"},
    }, children=ch)

    custom = {"period": "Daily", "selectedPoint": "A", "startDate": None, "endDate": None, "data": {}}
    pc = {
        "custom.period": {"persistent": True},
        "custom.selectedPoint": {"persistent": True},
        "custom.startDate": {"persistent": True},
        "custom.endDate": {"persistent": True},
        "custom.data": {
            "persistent": True,
            "binding": {
                "type": "expr-struct",
                "config": {
                    "struct": {
                        "period": "{view.custom.period}",
                        "start": "{view.custom.startDate}",
                        "end": "{view.custom.endDate}",
                        "point": "{view.custom.selectedPoint}",
                        "tick": "now(10000)",
                    },
                    "waitOnAll": True,
                },
                "transforms": [{
                    "type": "script",
                    "code": "\treturn hub4x4.data.getDashboard(value['period'], value['start'], value['end'], value['point'])",
                }],
            },
        },
    }
    events = {"system": {"onStartup": script("hub4x4.data.applyPeriod(self, 'Daily')")}}
    return view(root, {"width": DESIGN_W, "height": DESIGN_H}, custom=custom, propConfig=pc, events=events)


def write_page_config():
    d = os.path.join(PERSP, "page-config")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "config.json"), "w") as f:
        json.dump({"pages": {"/": {"title": "HUB 4x4 Quality", "viewPath": "HUB4x4/QualityDashboard"}},
                   "sharedDocks": {}}, f, indent=2)
    write_resource(d, "config.json")


if __name__ == "__main__":
    write_view("HUB4x4/QualityDashboard", build_dashboard())
    write_view("HUB4x4/Components/KpiTile", build_kpi_tile())
    write_view("HUB4x4/Components/BarRow", build_bar_row())
    write_view("HUB4x4/Components/LineStatusRow", build_line_row())
    write_view("HUB4x4/Components/AbnormalItem", build_abnormal_item())
    write_view("HUB4x4/Popups/AbnormalDetail", build_abnormal_popup())
    write_page_config()
    print("views written to", os.path.normpath(PERSP))
