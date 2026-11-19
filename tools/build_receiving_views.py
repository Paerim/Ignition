#!/usr/bin/env python3
"""
Generates the Perspective views of the Receiving station.

    python3 tools/build_receiving_views.py

    Receiving/SmartTV    page /receiving/tv        Truck Receiving Monitoring + Mini WMS (1920 x 1080)
    Receiving/HMI        page /receiving/hmi       Truck Arrive / Truck Departure buttons + Supplier dropdown
    Receiving/Handheld   page /receiving/handheld  CCR orders split per supplier, scan, confirm receipt
    Receiving/Overview   page /receiving           Links to the three screens

Data comes from the project script receiving.data (ignition/script-python/receiving/data).
"""
from build_views import (P, F, comp, prop, expr, script, label, flex, write_view, view, write_page_config)

NAVY = "#14304A"
NAVY2 = "#1D4466"
PAGE_BG = "#EEF2F6"
CARD = "#FFFFFF"
INK = "#1F2D3D"
MUTED = "#6B7A89"
LINE = "#D9E1E8"
GREEN = "#2DB84B"
RED = "#E53935"
BLUE = "#2E86DE"
ORANGE = "#F2994A"
YELLOW = "#FFE45C"
PILL_OFF = "#E4E8EC"
FONT = "Segoe UI, Tahoma, Arial, sans-serif"
STATUS_COLORS = [("On time", GREEN), ("Delay", RED), ("Advance", BLUE)]
SEQ_COLORS = {"A": "#1F6FA8", "B": "#23864A", "C": "#E07B12"}

TV_W, TV_H = 1920, 1080
HMI_W, HMI_H = 800, 480


def card(**extra):
    s = {"backgroundColor": CARD, "borderRadius": "10px", "boxShadow": "0 1px 4px rgba(20,48,74,0.18)",
         "overflow": "hidden"}
    s.update(extra)
    return s


def repeater(name, path, source, direction="column", position=None, element=None, style=None,
             transforms=None, default_w=False, default_h=True, wrap=None):
    p = {"path": path, "direction": direction, "instances": [],
         "useDefaultViewWidth": default_w, "useDefaultViewHeight": default_h,
         "elementPosition": element or {"basis": "auto", "grow": 0, "shrink": 0},
         "style": style or {}}
    if wrap:
        p["wrap"] = wrap
    return comp("ia.display.flex-repeater", name, p, position, {"props.instances": prop(source, transforms)})


def tscript(body):
    """Script transform."""
    return [{"type": "script", "code": "\n".join("\t" + l for l in body.strip("\n").split("\n"))}]


def table_col(field, title, width, justify="left"):
    return {
        "field": field, "visible": True, "editable": False, "render": "auto",
        "justify": justify, "align": "center", "resizable": False, "sortable": False, "sort": "none",
        "filter": {"enabled": False, "visible": "on-hover"},
        "viewPath": "", "viewParams": {}, "boolean": "checkbox", "number": "value",
        "numberFormat": "0,0", "dateFormat": "MM/DD/YYYY", "width": width, "strictWidth": False,
        "style": {"classes": ""},
        "header": {"title": title, "justify": justify, "align": "center", "style": {"classes": ""}},
        "footer": {"title": "", "justify": "left", "align": "center", "style": {"classes": ""}},
        "nullFormat": {"includeNullStrings": False, "strict": False, "nullFormatValue": ""},
    }


def table(name, source, columns, position, font="15px"):
    return comp("ia.display.table", name, {
        "data": [], "columns": columns,
        "pager": {"top": False, "bottom": False},
        "selection": {"enableRowSelection": False},
        "headerStyle": {"backgroundColor": "#F3F6F9", "color": MUTED, "fontSize": "13px", "fontWeight": "bold"},
        "rows": {"striped": {"enabled": True, "color": {"odd": "#FFFFFF", "even": "#F7F9FB"}},
                 "style": {"fontSize": font, "color": INK}},
        "style": {"borderStyle": "none"},
    }, position, {"props.data": prop(source)})


def status_pills(path, size="15px", width="92px"):
    """Three pills On time / Delay / Advance; the one equal to {path} is coloured."""
    pills = []
    for st, color in STATUS_COLORS:
        on = "{%s} = '%s'" % (path, st)
        pills.append(label("P" + st.replace(" ", ""), st, {
            "fontSize": size, "textAlign": "center", "borderRadius": "6px", "fontWeight": "bold",
            "border": "1px solid #C9D1D9", "margin": "0 3px"}, F(width), {
            "props.style.backgroundColor": expr("if(%s, '%s', '%s')" % (on, color, PILL_OFF)),
            "props.style.color": expr("if(%s, '#FFFFFF', '#5B6670')" % on),
            "props.style.borderColor": expr("if(%s, '%s', '#C9D1D9')" % (on, color)),
        }))
    return pills


# ================================================================== components
def build_truck_row():
    pr = "view.params."

    def actual(name, field):
        return flex(name + "Cell", [
            label(name, "", {"fontSize": "20px", "fontWeight": "bold", "textAlign": "center",
                             "borderRadius": "5px", "border": "1px solid transparent"}, F("90px"), {
                "props.text": expr("if(len({%s%s}) > 0, {%s%s}, '--')" % (pr, field, pr, field)),
                "props.style.backgroundColor": expr("if(len({%s%s}) > 0, '%s', 'transparent')" % (pr, field, YELLOW)),
                "props.style.borderColor": expr("if(len({%s%s}) > 0, '#C9A800', 'transparent')" % (pr, field)),
                "props.style.color": expr("if(len({%s%s}) > 0, '%s', '#A0AAB4')" % (pr, field, INK)),
            }),
        ], "row", {"justifyContent": "center", "alignItems": "center"}, F("120px"))

    root = flex("root", [
        flex("SupplierCell", [
            label("Supplier", "", {"fontSize": "21px", "fontWeight": "bold", "color": INK}, F("auto"),
                  {"props.text": prop(pr + "supplier")}),
            label("Pattern", "", {"fontSize": "15px", "color": MUTED}, F("auto"),
                  {"props.text": prop(pr + "pattern")}),
        ], "column", {"justifyContent": "center", "paddingLeft": "14px"}, F("140px")),
        label("Truck", "", {"fontSize": "19px", "color": INK, "textAlign": "center"}, F("120px"),
              {"props.text": prop(pr + "truckNo")}),
        label("ArrivePlan", "", {"fontSize": "20px", "color": INK, "textAlign": "center",
                                 "borderLeft": "1px solid " + LINE}, F("110px"),
              {"props.text": prop(pr + "arrivePlan")}),
        actual("ArriveActual", "arriveActual"),
        label("DepartPlan", "", {"fontSize": "20px", "color": INK, "textAlign": "center",
                                 "borderLeft": "1px solid " + LINE}, F("110px"),
              {"props.text": prop(pr + "departPlan")}),
        actual("DepartActual", "departActual"),
        flex("Status", status_pills(pr + "status", "16px", "100px"), "row",
             {"justifyContent": "center", "alignItems": "center", "borderLeft": "1px solid " + LINE},
             F("0", 1, 1)),
    ], "row", {"alignItems": "stretch", "backgroundColor": CARD})
    root["propConfig"] = {"props.style.borderTop": expr(
        "if({view.params.firstInGroup}, '2px solid #9FB0C0', '1px solid %s')" % LINE)}
    return view(root, {"width": 1060, "height": 58}, {
        "supplier": "ABC", "pattern": "1:2:2", "firstInGroup": True, "truckNo": "Truck01",
        "arrivePlan": "08:15", "arriveActual": "08:17", "departPlan": "08:20", "departActual": "",
        "arriveStatus": "On time", "departStatus": "", "status": "On time"})


def build_mini_kpi():
    root = flex("root", [
        label("Title", "", {"fontSize": "15px", "textAlign": "left", "color": INK}, F("auto", 0, 0),
              {"props.text": prop("view.params.title")}),
        label("Value", "", {"fontSize": "38px", "fontWeight": "bold", "textAlign": "left"}, F("auto", 1, 1),
              {"props.text": prop("view.params.value"), "props.style.color": prop("view.params.fg")}),
    ], "column", {"borderRadius": "8px", "padding": "8px 12px", "border": "1px solid rgba(0,0,0,0.06)"})
    root["propConfig"] = {"props.style.backgroundColor": prop("view.params.bg")}
    return view(root, {"width": 120, "height": 100},
                {"title": "ออเดอร์", "value": 0, "bg": "#E3F0FB", "fg": "#1F6FA8"})


def build_model_bar():
    root = flex("root", [
        label("Name", "", {"color": INK, "fontSize": "16px", "whiteSpace": "nowrap"}, F("80px"),
              {"props.text": prop("view.params.name")}),
        comp("ia.display.progress", "Bar", {
            "value": 0, "min": 0, "max": 100, "bar": {"color": "#1F6FA8"}, "track": {"color": "#E6EDF3"},
            "valueDisplay": {"enabled": False}, "style": {"height": "18px", "borderRadius": "9px"},
        }, F("auto", 1, 1), {"props.value": prop("view.params.value"), "props.max": prop("view.params.max")}),
        label("Text", "", {"color": INK, "fontSize": "16px", "textAlign": "right", "fontWeight": "bold"}, F("70px"),
              {"props.text": prop("view.params.text")}),
    ], "row", {"alignItems": "center", "gap": "8px"})
    return view(root, {"width": 330, "height": 34}, {"name": "Model A", "value": 9, "max": 11, "text": "9 คัน"})


def build_seq_chip():
    root = flex("root", [
        label("L", "", {"color": "#FFFFFF", "fontSize": "20px", "fontWeight": "bold", "textAlign": "center"},
              F("auto", 1, 1), {"props.text": prop("view.params.letter")}),
    ], "row", {"borderRadius": "5px", "alignItems": "center", "margin": "2px"})
    root["propConfig"] = {"props.style.backgroundColor": expr(
        "case({view.params.letter}, %s, '#888888')" % ", ".join("'%s', '%s'" % kv for kv in SEQ_COLORS.items()))}
    return view(root, {"width": 30, "height": 36}, {"letter": "A"})


def build_hmi_truck_card():
    pr = "view.params."
    color = "case({%sstatus}, %s, '#B0BAC4')" % (pr, ", ".join("'%s', '%s'" % kv for kv in STATUS_COLORS))
    root = flex("root", [
        label("Truck", "", {"fontSize": "14px", "fontWeight": "bold", "color": INK}, F("auto"),
              {"props.text": prop(pr + "truckNo")}),
        label("In", "", {"fontSize": "12px", "color": INK}, F("auto"),
              {"props.text": expr("concat('IN  ', {%sarrivePlan}, ' > ', if(len({%sarriveActual}) > 0, {%sarriveActual}, '--'))"
                                  % (pr, pr, pr))}),
        label("Out", "", {"fontSize": "12px", "color": INK}, F("auto"),
              {"props.text": expr("concat('OUT ', {%sdepartPlan}, ' > ', if(len({%sdepartActual}) > 0, {%sdepartActual}, '--'))"
                                  % (pr, pr, pr))}),
        label("Status", "", {"fontSize": "12px", "fontWeight": "bold", "color": "#FFFFFF", "textAlign": "center",
                             "borderRadius": "4px"}, F("18px"),
              {"props.text": expr("if(len({%sstatus}) > 0, {%sstatus}, 'Waiting')" % (pr, pr)),
               "props.style.backgroundColor": expr(color)}),
    ], "column", {"backgroundColor": "#F7F9FB", "border": "1px solid " + LINE, "borderRadius": "6px",
                  "padding": "4px 8px", "margin": "0 4px"})
    return view(root, {"width": 150, "height": 80}, {
        "truckNo": "Truck01", "arrivePlan": "08:15", "arriveActual": "", "departPlan": "08:20",
        "departActual": "", "status": ""})


def build_order_card():
    pr = "view.params."
    select = script("system.perspective.sendMessage('rcvSelectOrder', {'orderNo': self.view.params.orderNo}, scope='page')")
    root = flex("root", [
        flex("Top", [
            label("OrderNo", "", {"fontSize": "14px", "fontWeight": "bold", "color": INK}, F("auto", 1, 1),
                  {"props.text": prop(pr + "orderNo")}),
            label("Status", "", {"fontSize": "11px", "color": "#FFFFFF", "borderRadius": "10px",
                                 "padding": "0 8px", "textAlign": "center", "whiteSpace": "nowrap"}, F("auto"),
                  {"props.text": prop(pr + "statusText"), "props.style.backgroundColor": prop(pr + "statusColor")}),
        ], "row", {"alignItems": "center"}, F("22px")),
        label("Supplier", "", {"fontSize": "13px", "color": MUTED}, F("18px"),
              {"props.text": expr("concat({%ssupplierName}, '  -  ', {%sparts}, ' รายการ')" % (pr, pr))}),
        flex("Prog", [
            comp("ia.display.progress", "Bar", {
                "value": 0, "max": 1, "bar": {"color": GREEN}, "track": {"color": "#E6EDF3"},
                "valueDisplay": {"enabled": False}, "style": {"height": "8px", "borderRadius": "4px"},
            }, F("auto", 1, 1), {"props.value": prop(pr + "scanned"), "props.max": prop(pr + "qty")}),
            label("Qty", "", {"fontSize": "13px", "color": INK, "textAlign": "right"}, F("80px"),
                  {"props.text": expr("concat({%sscanned}, ' / ', {%sqty}, ' ชิ้น')" % (pr, pr))}),
        ], "row", {"alignItems": "center", "gap": "8px"}, F("22px")),
    ], "column", {"borderRadius": "8px", "padding": "8px 10px", "margin": "4px 0", "cursor": "pointer",
                  "backgroundColor": "#F7F9FB"})
    root["propConfig"] = {"props.style.border": expr(
        "if({view.params.selected}, '2px solid %s', '1px solid %s')" % (BLUE, LINE))}
    root["events"] = {"dom": {"onClick": select}}
    return view(root, {"width": 360, "height": 86}, {
        "orderNo": "CCR-20261119-01-ABC", "supplier": "ABC", "supplierName": "ABC Co., Ltd.", "parts": 2,
        "qty": 40, "scanned": 0, "statusText": "รอรับเข้า", "statusColor": ORANGE, "selected": False})


def build_item_row():
    pr = "view.params."
    root = flex("root", [
        flex("Name", [
            label("Part", "", {"fontSize": "14px", "fontWeight": "bold", "color": INK}, F("auto"),
                  {"props.text": prop(pr + "partNo")}),
            label("Desc", "", {"fontSize": "12px", "color": MUTED}, F("auto"), {"props.text": prop(pr + "name")}),
        ], "column", {"justifyContent": "center"}, F("110px")),
        comp("ia.display.progress", "Bar", {
            "value": 0, "max": 1, "bar": {"color": BLUE}, "track": {"color": "#E6EDF3"},
            "valueDisplay": {"enabled": False}, "style": {"height": "10px", "borderRadius": "5px"},
        }, F("auto", 1, 1), {"props.value": prop(pr + "scanned"), "props.max": prop(pr + "qty"),
                             "props.bar.color": expr("if({%sdone}, '%s', '%s')" % (pr, GREEN, BLUE))}),
        label("Qty", "", {"fontSize": "15px", "fontWeight": "bold", "color": INK, "textAlign": "right"}, F("70px"),
              {"props.text": expr("concat({%sscanned}, '/', {%sqty})" % (pr, pr))}),
        comp("ia.display.icon", "Ok", {"path": "material/check_circle", "color": GREEN, "style": {}}, F("24px"),
             {"props.color": expr("if({%sdone}, '%s', '#D0D7DE')" % (pr, GREEN))}),
    ], "row", {"alignItems": "center", "gap": "8px", "padding": "6px 8px", "borderBottom": "1px solid " + LINE})
    root["propConfig"] = {"props.style.backgroundColor": expr("if({view.params.done}, '#EEF9F0', '#FFFFFF')")}
    return view(root, {"width": 360, "height": 52},
                {"partNo": "T0001", "name": "CABIN", "qty": 20, "scanned": 0, "done": False})


# ================================================================== Smart TV
def build_smart_tv():
    D = "view.custom.data."
    ch = []
    # header
    ch.append(flex("Header", [
        comp("ia.display.icon", "Icon", {"path": "material/local_shipping", "color": "#FFFFFF"}, F("44px")),
        label("Title", "Receiving Dashboard", {"color": "#FFFFFF", "fontSize": "32px", "fontWeight": "bold",
                                              "paddingLeft": "12px"}, F("auto", 1, 1)),
        label("Date", "", {"color": "#C9D8E6", "fontSize": "22px", "textAlign": "right"}, F("220px"),
              {"props.text": expr("concat('Date : ', dateFormat(now(1000), 'dd/MM/yyyy'))")}),
        label("Time", "", {"color": "#FFFFFF", "fontSize": "26px", "fontWeight": "bold", "textAlign": "right",
                           "paddingRight": "24px"}, F("210px"),
              {"props.text": expr("concat('Time : ', dateFormat(now(1000), 'HH:mm:ss'))")}),
    ], "row", {"backgroundColor": NAVY, "alignItems": "center", "paddingLeft": "24px"}, P(0, 0, TV_W, 72, TV_W, TV_H)))

    # ---- (1) Truck Receiving Monitoring
    def summary_chip(name, text, color, path):
        return label(name, "", {"color": "#FFFFFF", "fontSize": "17px", "fontWeight": "bold", "textAlign": "center",
                                "backgroundColor": color, "borderRadius": "16px", "margin": "0 4px"},
                     F("130px"), {"props.text": expr("concat('%s  ', {%s})" % (text, D + path))})

    def hcell(name, text, basis, **st):
        s = {"color": "#FFFFFF", "fontSize": "18px", "fontWeight": "bold", "textAlign": "center"}
        s.update(st)
        return label(name, text, s, F(basis))

    def hgroup(name, title):
        return flex(name, [
            hcell("T", title, "34px", borderBottom="1px solid #4C6E8E"),
            flex("Sub", [hcell("Plan", "Plan", "110px", fontSize="16px"),
                         hcell("Actual", "Actual", "120px", fontSize="16px")], "row", {}, F("auto", 1, 1)),
        ], "column", {"borderLeft": "1px solid #4C6E8E"}, F("230px"))

    truck = flex("TruckMonitoring", [
        flex("TitleRow", [
            label("Badge", "1", {"color": "#FFFFFF", "backgroundColor": NAVY, "borderRadius": "50%",
                                 "textAlign": "center", "fontSize": "18px", "fontWeight": "bold"}, F("32px")),
            label("Title", "Truck Receiving Monitoring", {"color": INK, "fontSize": "28px", "fontWeight": "bold",
                                                         "paddingLeft": "12px"}, F("auto", 1, 1)),
            summary_chip("SumOnTime", "On time", GREEN, "summary.onTime"),
            summary_chip("SumDelay", "Delay", RED, "summary.delay"),
            summary_chip("SumAdvance", "Advance", BLUE, "summary.advance"),
        ], "row", {"alignItems": "center", "padding": "0 16px"}, F("70px")),
        flex("TableHead", [
            flex("SupplierH", [hcell("T", "Supplier name", "auto", paddingLeft="14px", textAlign="left")],
                 "column", {"justifyContent": "center"}, F("140px")),
            flex("TruckH", [hcell("T", "Truck No.", "auto")], "column",
                 {"justifyContent": "center", "borderLeft": "1px solid #4C6E8E"}, F("120px")),
            hgroup("ArriveH", "Truck Arrive"),
            hgroup("DepartH", "Truck Departure"),
            flex("StatusH", [hcell("T", "Status", "auto")], "column",
                 {"justifyContent": "center", "borderLeft": "1px solid #4C6E8E"}, F("0", 1, 1)),
        ], "row", {"backgroundColor": NAVY2, "margin": "0 16px", "borderRadius": "8px 8px 0 0"}, F("68px")),
        repeater("Rows", "Receiving/Components/TruckRow", D + "trucks", position=F("auto", 1, 1),
                 style={"overflowY": "auto", "margin": "0 16px 12px 16px", "border": "1px solid " + LINE,
                        "borderTop": "none"}),
        flex("Legend", [
            label("L", "Actual (สีเหลือง) = เวลาจริงจากปุ่ม HMI / PLC     Tolerance ±5 นาที : On time  |  "
                       "ช้ากว่าแผน = Delay  |  เร็วกว่าแผน = Advance",
                  {"color": MUTED, "fontSize": "15px", "paddingLeft": "18px"}, F("auto", 1, 1)),
        ], "row", {"alignItems": "center"}, F("34px")),
    ], "column", card(), P(20, 88, 1120, 972, TV_W, TV_H))
    ch.append(truck)

    # ---- (2) Mini WMS
    W = "view.custom.data.wms."
    seg = []
    for nm, key, color in [("Open", "open", ORANGE), ("Receiving", "receiving", BLUE), ("Received", "received", GREEN)]:
        seg.append(flex(nm, [], "row", {"backgroundColor": color}, F("0px", 0, 1),
                        {"position.grow": prop(W + "orderStatus." + key)}))
    legend = []
    for nm, txt, key, color in [("LOpen", "รอรับเข้า", "open", ORANGE),
                                ("LReceiving", "กำลังรับเข้า", "receiving", BLUE),
                                ("LReceived", "รับสำเร็จ", "received", GREEN)]:
        legend.append(label(nm, "", {"fontSize": "15px", "color": INK, "paddingRight": "14px"}, F("auto"),
                            {"props.text": expr("concat('%s (', {%s}, ')')" % (txt, W + "orderStatus." + key))}))
        legend.insert(len(legend) - 1, flex("Dot" + nm, [], "row", {"backgroundColor": color, "borderRadius": "50%",
                                                                    "margin": "0 6px 0 0"}, F("12px")))
    sub_title = {"color": INK, "fontSize": "18px", "fontWeight": "bold"}

    wms = flex("MiniWms", [
        flex("TitleRow", [
            label("Badge", "2", {"color": "#FFFFFF", "backgroundColor": NAVY, "borderRadius": "50%",
                                 "textAlign": "center", "fontSize": "18px", "fontWeight": "bold"}, F("32px")),
            label("Title", "Mini WMS", {"color": INK, "fontSize": "28px", "fontWeight": "bold",
                                        "paddingLeft": "12px"}, F("auto", 1, 1)),
            label("Sub", "", {"color": MUTED, "fontSize": "16px", "textAlign": "right"}, F("auto"),
                  {"props.text": expr("concat('การทำงานวันนี้  |  CCR : ', {%sccrOrderNo})" % W)}),
        ], "row", {"alignItems": "center"}, F("56px")),
        repeater("Kpi", "Receiving/Components/MiniKpi", W + "kpi", "row", F("108px"),
                 {"basis": "0px", "grow": 1, "shrink": 1}, {"gap": "8px"}, default_h=False),
        flex("Mid", [
            flex("OrderStatus", [
                label("T", "สถานะออเดอร์ทั้งหมด", sub_title, F("30px")),
                flex("Bar", seg, "row", {"backgroundColor": "#E6EDF3", "borderRadius": "9px", "overflow": "hidden"},
                     F("18px")),
                flex("Legend", legend, "row", {"alignItems": "center", "flexWrap": "wrap", "marginTop": "10px"},
                     F("auto")),
                label("Total", "", {"color": MUTED, "fontSize": "14px", "marginTop": "6px"}, F("auto"),
                      {"props.text": expr("concat('ออเดอร์ Supplier ทั้งหมด ', {%sorderStatus.total}, ' รายการ')" % W)}),
            ], "column", {"border": "1px solid " + LINE, "borderRadius": "8px", "padding": "10px 12px"},
                F("0", 1, 1)),
            flex("Models", [
                label("T", "ผลิตตามโมเดล", sub_title, F("30px")),
                repeater("Bars", "Receiving/Components/ModelBar", W + "models", position=F("auto", 1, 1),
                         style={"justifyContent": "space-around"}),
            ], "column", {"border": "1px solid " + LINE, "borderRadius": "8px", "padding": "10px 12px"},
                F("0", 1, 1)),
        ], "row", {"gap": "12px", "marginTop": "12px"}, F("170px")),
        flex("Sequence", [
            flex("Head", [
                label("T", "Production Sequence จาก CCR", sub_title, F("auto", 1, 1)),
                label("Legend", "A = Model A   B = Model B   C = Model C", {"color": MUTED, "fontSize": "14px"},
                      F("auto")),
            ], "row", {"alignItems": "center"}, F("30px")),
            flex("Result", [
                label("R", "Result", {"color": INK, "fontSize": "16px", "fontWeight": "bold"}, F("62px")),
                repeater("Chips", "Receiving/Components/SeqChip", W + "sequence", "row", F("auto", 1, 1),
                         {"basis": "0px", "grow": 1, "shrink": 1}, {"backgroundColor": NAVY, "borderRadius": "6px",
                                                                    "padding": "4px"},
                         tscript("return [{'letter': c} for c in (value or '')]"), default_h=False),
            ], "row", {"alignItems": "center"}, F("46px")),
        ], "column", {"border": "1px solid " + LINE, "borderRadius": "8px", "padding": "10px 12px",
                      "marginTop": "12px"}, F("110px")),
        flex("Parts", [
            label("T", "รายการ Part ที่ต้องรับเข้า (แจกแจงตาม Order)", sub_title, F("34px")),
            table("Table", W + "parts", [
                table_col("partNo", "Item Code", 90),
                table_col("name", "ชื่อสินค้า", 150),
                table_col("supplier", "Supplier", 80, "center"),
                table_col("qty", "จำนวนสั่ง", 80, "right"),
                table_col("received", "รับแล้ว", 70, "right"),
                table_col("remain", "คงเหลือ", 70, "right"),
            ], F("auto", 1, 1), "16px"),
        ], "column", {"border": "1px solid " + LINE, "borderRadius": "8px", "padding": "10px 12px",
                      "marginTop": "12px"}, F("auto", 1, 1)),
    ], "column", card(padding="8px 16px 16px 16px"), P(1160, 88, 740, 972, TV_W, TV_H))
    ch.append(wms)

    root = comp("ia.container.coord", "root", {"mode": "percent",
                                               "style": {"backgroundColor": PAGE_BG, "fontFamily": FONT}},
                children=ch)
    pc = {"custom.data": {"persistent": True, "binding": {
        "type": "expr", "config": {"expression": "now(5000)"},
        "transforms": tscript("return receiving.data.getTv()")}}}
    return view(root, {"width": TV_W, "height": TV_H}, custom={"data": {}}, propConfig=pc)


# ================================================================== HMI
def build_hmi():
    D = "view.custom.data."
    ch = []
    ch.append(flex("Header", [
        label("Title", "Receiving HMI", {"color": "#FFFFFF", "fontSize": "22px", "fontWeight": "bold"}, F("auto", 1, 1)),
        label("Clock", "", {"color": "#C9D8E6", "fontSize": "16px", "textAlign": "right"}, F("auto"),
              {"props.text": expr("dateFormat(now(1000), 'dd/MM/yyyy HH:mm:ss')")}),
    ], "row", {"backgroundColor": NAVY, "alignItems": "center", "padding": "0 16px"}, P(0, 0, HMI_W, 46, HMI_W, HMI_H)))

    dd_style = {"fontSize": "18px"}
    ch.append(flex("Select", [
        label("L1", "Supplier", {"color": INK, "fontSize": "16px", "fontWeight": "bold"}, F("78px")),
        comp("ia.input.dropdown", "Supplier", {"options": [], "placeholder": {"text": "เลือก Supplier"},
                                               "search": {"enabled": False}, "showClearIcon": False,
                                               "style": dd_style}, F("0", 1, 1), {
            "props.options": prop(D + "suppliers"),
            "props.value": prop("view.custom.supplier", bidirectional=True)}),
        label("L2", "Truck", {"color": INK, "fontSize": "16px", "fontWeight": "bold", "paddingLeft": "14px"},
              F("66px")),
        comp("ia.input.dropdown", "Truck", {"options": [], "search": {"enabled": False}, "showClearIcon": False,
                                            "style": dd_style}, F("0", 1, 1), {
            "props.options": prop(D + "trucks", tscript(
                "return [{'value': '', 'label': 'Auto (คันถัดไป)'}] + "
                "[{'value': t['truckNo'], 'label': t['truckNo']} for t in (value or [])]")),
            "props.value": prop("view.custom.truckNo", bidirectional=True)}),
    ], "row", {"alignItems": "center", "gap": "6px"}, P(16, 54, 768, 44, HMI_W, HMI_H)))

    def tile(name, title, kind, bar_color, icons, can):
        action = script("""
res = receiving.data.stampTruck(self.view.custom.supplier, self.view.custom.truckNo, '%s')
self.view.custom.message = res['message']
self.view.custom.messageOk = res['ok']
self.view.custom.truckNo = ''
self.view.custom.rev = self.view.custom.rev + 1
""" % kind)
        t = flex(name, [
            flex("IconBox", icons, "row", {"backgroundColor": "#F4F6F8", "border": "2px solid " + NAVY,
                                           "borderRadius": "16px", "justifyContent": "center",
                                           "alignItems": "center", "margin": "0 0 6px 0"}, F("auto", 1, 1)),
            label("Label", title, {"color": "#FFFFFF", "fontSize": "26px", "fontWeight": "bold", "textAlign": "center",
                                   "backgroundColor": bar_color, "borderRadius": "10px"}, F("58px")),
        ], "column", {"cursor": "pointer"}, None, )
        t["propConfig"] = {"props.style.opacity": expr("if({%s}, 1, 0.45)" % (D + can))}
        t["events"] = {"dom": {"onClick": action}}
        return t

    arrive_icons = [
        comp("ia.display.icon", "Clock", {"path": "material/schedule", "color": "#2B2B2B",
                                          "style": {"marginTop": "-60px"}}, F("56px")),
        comp("ia.display.icon", "Truck", {"path": "material/local_shipping", "color": "#5AA9E6"}, F("150px")),
    ]
    depart_icons = [
        comp("ia.display.icon", "Truck", {"path": "material/local_shipping", "color": "#F2B33D",
                                          "style": {"transform": "scaleX(-1)"}}, F("150px")),
        comp("ia.display.icon", "Go", {"path": "material/double_arrow", "color": "#B04A2E"}, F("56px")),
    ]
    a = tile("BtnArrive", "Truck Arrive", "arrive", "#3E8E2E", arrive_icons, "canArrive")
    a["position"] = P(16, 106, 376, 236, HMI_W, HMI_H)
    d = tile("BtnDeparture", "Truck Departure", "depart", NAVY, depart_icons, "canDepart")
    d["position"] = P(408, 106, 376, 236, HMI_W, HMI_H)
    ch += [a, d]

    ch.append(label("Message", "", {"fontSize": "16px", "fontWeight": "bold", "borderRadius": "6px",
                                    "paddingLeft": "12px"}, P(16, 348, 768, 34, HMI_W, HMI_H), {
        "props.text": expr("if(len({view.custom.message}) > 0, {view.custom.message}, "
                           "'เลือก Supplier แล้วกดปุ่ม Truck Arrive / Truck Departure')"),
        "props.style.backgroundColor": expr("if(len({view.custom.message}) = 0, '#EEF2F6', "
                                            "if({view.custom.messageOk}, '#E6F6EA', '#FCE8E6'))"),
        "props.style.color": expr("if(len({view.custom.message}) = 0, '%s', "
                                  "if({view.custom.messageOk}, '#23864A', '#C62828'))" % MUTED),
    }))
    ch.append(repeater("Trucks", "Receiving/Components/HmiTruckCard", D + "trucks", "row",
                       P(12, 388, 776, 84, HMI_W, HMI_H), {"basis": "150px", "grow": 0, "shrink": 0},
                       {"overflowX": "auto"}, default_h=False))

    root = comp("ia.container.coord", "root", {"mode": "percent",
                                               "style": {"backgroundColor": "#FFFFFF", "fontFamily": FONT}},
                children=ch)
    custom = {"supplier": "ABC", "truckNo": "", "message": "", "messageOk": True, "rev": 0, "data": {}}
    pc = {
        "custom.supplier": {"persistent": True}, "custom.truckNo": {"persistent": True},
        "custom.message": {"persistent": True}, "custom.messageOk": {"persistent": True},
        "custom.rev": {"persistent": True},
        "custom.data": {"persistent": True, "binding": {
            "type": "expr-struct",
            "config": {"struct": {"supplier": "{view.custom.supplier}", "rev": "{view.custom.rev}",
                                  "tick": "now(5000)"}, "waitOnAll": True},
            "transforms": tscript("return receiving.data.getHmi(value['supplier'])")}},
    }
    return view(root, {"width": HMI_W, "height": HMI_H}, custom=custom, propConfig=pc)


# ================================================================== Handheld
def build_handheld():
    D = "view.custom.data."
    sec_title = {"color": INK, "fontSize": "15px", "fontWeight": "bold"}

    def section(name, children, basis="auto", **st):
        s = card(padding="10px 12px", margin="8px 10px 0 10px", overflow="visible")
        s.update(st)
        return flex(name, children, "column", s, F(basis))

    def msg_label(name, text_path, ok_path):
        return label(name, "", {"fontSize": "14px", "fontWeight": "bold", "borderRadius": "6px", "padding": "6px 8px",
                                "marginTop": "6px"}, F("auto"), {
            "props.text": prop(text_path),
            "meta.visible": expr("len({%s}) > 0" % text_path),
            "props.style.backgroundColor": expr("if({%s}, '#E6F6EA', '#FCE8E6')" % ok_path),
            "props.style.color": expr("if({%s}, '#23864A', '#C62828')" % ok_path),
        })

    pull = script("""
res = receiving.data.pullCcrOrders()
self.view.custom.ccrMsg = res['message']
self.view.custom.ccrOk = res['ok']
self.view.custom.rev = self.view.custom.rev + 1
""")
    confirm = script("""
res = receiving.data.confirmReceive(self.view.custom.orderNo)
self.view.custom.scanMsg = res['message']
self.view.custom.scanOk = res['ok']
self.view.custom.rev = self.view.custom.rev + 1
""")
    scan_btn = script("""
v = self.getSibling('ScanInput').props.text
if v:
	self.view.custom.scanText = v
""")
    btn = {"fontSize": "15px", "borderRadius": "8px", "border": "none", "color": "#FFFFFF"}

    children = [
        flex("Header", [
            comp("ia.display.icon", "Icon", {"path": "material/qr_code_scanner", "color": "#FFFFFF"}, F("28px")),
            label("Title", "Receiving Handheld", {"color": "#FFFFFF", "fontSize": "18px", "fontWeight": "bold",
                                                  "paddingLeft": "8px"}, F("auto", 1, 1)),
            label("Updated", "", {"color": "#C9D8E6", "fontSize": "12px"}, F("auto"),
                  {"props.text": prop(D + "updated")}),
        ], "row", {"backgroundColor": NAVY, "alignItems": "center", "padding": "0 12px"}, F("52px")),

        section("Ccr", [
            flex("Row", [
                flex("Info", [
                    label("T", "ออเดอร์ล่าสุดจาก CCR", sec_title, F("auto")),
                    label("No", "", {"color": MUTED, "fontSize": "13px"}, F("auto"),
                          {"props.text": expr("concat({%sccr.orderNo}, '  (', len({%sccr.sequence}), ' คัน)')"
                                              % (D, D))}),
                ], "column", {}, F("auto", 1, 1)),
                comp("ia.input.button", "Pull", {"text": "รับออเดอร์จาก CCR", "image": {"icon": {
                    "path": "material/cloud_download", "color": "#FFFFFF"}},
                    "style": dict(btn, backgroundColor=BLUE)}, F("170px"),
                     events={"component": {"onActionPerformed": pull}}),
            ], "row", {"alignItems": "center", "gap": "8px"}, F("auto")),
            label("Seq", "", {"fontFamily": "Consolas, monospace", "fontSize": "15px", "letterSpacing": "2px",
                              "color": "#FFFFFF", "backgroundColor": NAVY2, "borderRadius": "6px",
                              "padding": "4px 8px", "marginTop": "6px", "wordBreak": "break-all"}, F("auto"),
                  {"props.text": expr("concat('Sequence : ', {%sccr.sequence})" % D)}),
            msg_label("Msg", "view.custom.ccrMsg", "view.custom.ccrOk"),
        ]),

        section("Orders", [
            label("T", "รายการที่ต้องรับเข้าวันนี้ (แยกตาม Supplier)", sec_title, F("24px")),
            label("Split", "", {"color": INK, "fontSize": "13px", "backgroundColor": "#F3F6F9", "borderRadius": "6px",
                                "padding": "4px 8px", "margin": "4px 0"}, F("auto"),
                  {"props.text": prop(D + "bySupplier", tscript(
                      "return '  |  '.join(['%s : %d ชิ้น' % (r['supplier'], r['qty']) for r in (value or [])])"))}),
            label("Hint", "แตะออเดอร์เพื่อดูรายการสินค้าที่ต้องรับเข้า", {"color": MUTED, "fontSize": "12px"},
                  F("18px")),
            repeater("List", "Receiving/Components/OrderCard", D + "orders", position=F("auto"),
                     style={"maxHeight": "290px", "overflowY": "auto"}),
        ]),

        section("Receive", [
            flex("Head", [
                flex("Info", [
                    label("Order", "", sec_title, F("auto"),
                          {"props.text": expr("if(len({%sselected.orderNo}) > 0, {%sselected.orderNo}, "
                                              "'ยังไม่ได้เลือกออเดอร์')" % (D, D))}),
                    label("Sup", "", {"color": MUTED, "fontSize": "13px"}, F("auto"),
                          {"props.text": prop(D + "selected.supplier")}),
                ], "column", {}, F("auto", 1, 1)),
                label("Status", "", {"color": "#FFFFFF", "fontSize": "12px", "fontWeight": "bold",
                                     "borderRadius": "10px", "padding": "2px 10px", "whiteSpace": "nowrap"}, F("auto"), {
                    "props.text": expr("concat({%sselected.statusText}, if(len({%sselected.confirmedAt}) > 0, "
                                       "concat(' ', {%sselected.confirmedAt}), ''))" % (D, D, D)),
                    "props.style.backgroundColor": prop(D + "selected.statusColor"),
                    "meta.visible": expr("len({%sselected.orderNo}) > 0" % D)}),
            ], "row", {"alignItems": "center"}, F("auto")),
            flex("ScanRow", [
                comp("ia.input.text-field", "ScanInput", {
                    "placeholder": "สแกน / พิมพ์ Part No. (เช่น T0001 หรือ T0001*5)", "deferUpdates": True,
                    "style": {"fontSize": "16px"}}, F("auto", 1, 1),
                    {"props.text": prop("view.custom.scanText", bidirectional=True),
                     "props.enabled": expr("{%sselected.status} != 'RECEIVED' && len({%sselected.orderNo}) > 0"
                                           % (D, D))}),
                comp("ia.input.button", "ScanBtn", {"text": "สแกน", "image": {"icon": {
                    "path": "material/qr_code_scanner", "color": "#FFFFFF"}},
                    "style": dict(btn, backgroundColor=NAVY)}, F("92px"),
                     events={"component": {"onActionPerformed": scan_btn}}),
            ], "row", {"gap": "6px", "marginTop": "8px"}, F("42px")),
            msg_label("ScanMsg", "view.custom.scanMsg", "view.custom.scanOk"),
            repeater("Items", "Receiving/Components/ItemRow", D + "items", position=F("auto"),
                     style={"marginTop": "6px", "border": "1px solid " + LINE, "borderRadius": "6px"}),
            label("Total", "", {"color": INK, "fontSize": "14px", "textAlign": "right", "marginTop": "6px"}, F("auto"), {
                "props.text": expr("concat('สแกนแล้ว ', {%sselected.scanned}, ' / ', {%sselected.qty}, ' ชิ้น')" % (D, D)),
                "meta.visible": expr("len({%sselected.orderNo}) > 0" % D)}),
            comp("ia.input.button", "Confirm", {"text": "ยืนยันรับสินค้า", "image": {"icon": {
                "path": "material/task_alt", "color": "#FFFFFF"}},
                "style": dict(btn, backgroundColor=GREEN, fontSize="18px", marginTop="8px")}, F("50px"), {
                "props.enabled": expr("len({%sselected.orderNo}) > 0 && {%sselected.status} != 'RECEIVED'" % (D, D))},
                 events={"component": {"onActionPerformed": confirm}}),
        ], marginBottom="12px"),
    ]
    root = flex("root", children, "column", {"backgroundColor": PAGE_BG, "fontFamily": FONT, "overflowY": "auto"})
    root["scripts"] = {"customMethods": [], "extensionFunctions": None, "messageHandlers": [{
        "messageType": "rcvSelectOrder", "pageScope": True, "sessionScope": False, "viewScope": False,
        "script": "\tself.view.custom.orderNo = payload['orderNo']\n\tself.view.custom.scanMsg = ''",
    }]}
    custom = {"orderNo": "", "scanText": "", "scanMsg": "", "scanOk": True, "ccrMsg": "", "ccrOk": True,
              "rev": 0, "data": {}}
    on_scan = "\n".join("\t" + l for l in """
v = currentValue.value if currentValue else None
if v:
	res = receiving.data.scanPart(self.custom.orderNo, v)
	self.custom.scanMsg = res['message']
	self.custom.scanOk = res['ok']
	self.custom.scanText = ''
	self.custom.rev = self.custom.rev + 1
""".strip("\n").split("\n"))
    pc = dict(("custom." + k, {"persistent": True}) for k in custom if k != "data")
    pc["custom.scanText"] = {"persistent": True, "onChange": {"enabled": None, "script": on_scan}}
    pc["custom.data"] = {"persistent": True, "binding": {
        "type": "expr-struct",
        "config": {"struct": {"orderNo": "{view.custom.orderNo}", "rev": "{view.custom.rev}", "tick": "now(5000)"},
                   "waitOnAll": True},
        "transforms": tscript("return receiving.data.getHandheld(value['orderNo'])")}}
    return view(root, {"width": 400, "height": 860}, custom=custom, propConfig=pc)


# ================================================================== Overview
def build_overview():
    def link(name, title, sub, icon, url, color):
        c = flex(name, [
            comp("ia.display.icon", "Icon", {"path": icon, "color": color}, F("90px")),
            label("T", title, {"color": INK, "fontSize": "22px", "fontWeight": "bold", "textAlign": "center"}, F("36px")),
            label("S", sub, {"color": MUTED, "fontSize": "14px", "textAlign": "center"}, F("auto", 1, 1)),
        ], "column", card(padding="20px", cursor="pointer", margin="12px", alignItems="center"),
            F("260px"))
        c["events"] = {"dom": {"onClick": script("system.perspective.navigate('%s')" % url)}}
        return c

    root = flex("root", [
        label("Title", "Receiving Station", {"color": "#FFFFFF", "fontSize": "28px", "fontWeight": "bold",
                                             "backgroundColor": NAVY, "paddingLeft": "24px"}, F("70px")),
        flex("Links", [
            link("Tv", "Smart TV", "Truck Receiving Monitoring + Mini WMS", "material/tv", "/receiving/tv", BLUE),
            link("Hmi", "HMI", "Truck Arrive / Truck Departure", "material/touch_app", "/receiving/hmi", GREEN),
            link("Handheld", "Handheld", "รับออเดอร์ CCR / สแกนรับสินค้า", "material/smartphone",
                 "/receiving/handheld", ORANGE),
        ], "row", {"justifyContent": "center", "alignItems": "flex-start", "flexWrap": "wrap", "padding": "30px"},
            F("auto", 1, 1)),
    ], "column", {"backgroundColor": PAGE_BG, "fontFamily": FONT})
    return view(root, {"width": 1000, "height": 500})


if __name__ == "__main__":
    write_view("Receiving/Components/TruckRow", build_truck_row())
    write_view("Receiving/Components/MiniKpi", build_mini_kpi())
    write_view("Receiving/Components/ModelBar", build_model_bar())
    write_view("Receiving/Components/SeqChip", build_seq_chip())
    write_view("Receiving/Components/HmiTruckCard", build_hmi_truck_card())
    write_view("Receiving/Components/OrderCard", build_order_card())
    write_view("Receiving/Components/ItemRow", build_item_row())
    write_view("Receiving/SmartTV", build_smart_tv())
    write_view("Receiving/HMI", build_hmi())
    write_view("Receiving/Handheld", build_handheld())
    write_view("Receiving/Overview", build_overview())
    write_page_config()
    print("receiving views written")
