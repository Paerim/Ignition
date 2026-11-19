"""
Receiving station - data provider for the three Receiving views.

    Smart TV  (Receiving/SmartTV)  : receiving.data.getTv()
    HMI       (Receiving/HMI)      : receiving.data.getHmi(supplier)
                                     receiving.data.stampTruck(supplier, truckNo, 'arrive' | 'depart')
    Handheld  (Receiving/Handheld) : receiving.data.getHandheld(orderNo)
                                     receiving.data.pullCcrOrders()
                                     receiving.data.scanPart(orderNo, code)
                                     receiving.data.confirmReceive(orderNo)

Order flow
    CCR sends an order = a production Sequence such as "ABCAABAABCABAABACABA"
    (one letter per unit, A/B/C = model).  receiveCcrOrder() explodes it with the BOM
    into one receiving order per Supplier (the parts that supplier must deliver).
    The handheld scans the parts of a supplier order and confirms the receipt.

Truck stamps
    The HMI buttons (or a PLC signal, see onPlcSignal) write the actual arrive /
    departure time of the next truck of the selected supplier.  Status is
    On time / Delay / Advance against the plan with +-TOLERANCE_MIN minutes.

Storage
    USE_DB = False : simulated, kept in memory (system.util.getGlobals), resets every day.
    USE_DB = True  : tables in db/receiving_schema.sql on connection DB.
"""
import random

USE_DB = False
DB = "Receiving"
TOLERANCE_MIN = 5

SUPPLIERS = [
	{"code": "ABC", "name": "ABC Co., Ltd.", "pattern": "1:2:2"},
	{"code": "DEF", "name": "DEF Co., Ltd.", "pattern": "1:1:1"},
	{"code": "XYZ", "name": "XYZ Co., Ltd.", "pattern": "1:3:3"},
]

# Daily truck plan used by the simulation (DB mode reads rcv_truck_plan)
TRUCK_PLAN = [
	("ABC", "Truck01", "08:15", "08:20"),
	("ABC", "Truck02", "09:15", "09:20"),
	("DEF", "Truck01", "14:15", "14:20"),
	("XYZ", "Truck01", "10:15", "10:20"),
	("XYZ", "Truck02", "13:15", "13:20"),
	("XYZ", "Truck03", "15:15", "15:20"),
]

# Part master: part no -> (name, supplier)
PARTS = {
	"T0001": ("CABIN", "ABC"),
	"T0002": ("CHASSIS", "ABC"),
	"T0003": ("WATER TANK", "DEF"),
	"T0004": ("CEMENT MIXER", "DEF"),
	"T0005": ("CRANE ARM", "XYZ"),
	"T0006": ("WHEEL SET", "XYZ"),
}
PART_ORDER = sorted(PARTS.keys())

# BOM: model -> [(part no, qty per unit)]
MODELS = ["A", "B", "C"]
BOM = {
	"A": [("T0001", 1), ("T0002", 1), ("T0005", 1), ("T0006", 2)],   # crane truck
	"B": [("T0001", 1), ("T0002", 1), ("T0003", 1), ("T0006", 2)],   # water truck
	"C": [("T0001", 1), ("T0002", 1), ("T0004", 1), ("T0006", 3)],   # mixer truck
}

STATUS_COLOR = {"On time": "#2DB84B", "Delay": "#E53935", "Advance": "#2E86DE"}
ORDER_STATUS = {
	"OPEN": ("รอรับเข้า", "#F2994A"),
	"RECEIVING": ("กำลังรับเข้า", "#2E86DE"),
	"RECEIVED": ("รับสินค้าสำเร็จ", "#2DB84B"),
}


# ================================================================= helpers
def _today():
	return system.date.format(system.date.now(), "yyyy-MM-dd")


def _hm(minutes):
	if minutes is None:
		return ""
	return "%02d:%02d" % (int(minutes) // 60, int(minutes) % 60)


def _min(hm):
	"""'HH:mm' or a Date -> minute of day."""
	if hm is None or hm == "":
		return None
	if hasattr(hm, "getTime"):
		return system.date.getHour24(hm) * 60 + system.date.getMinute(hm)
	h, m = str(hm).split(":")[:2]
	return int(h) * 60 + int(m)


def _nowMin():
	return _min(system.date.now())


def judge(planMin, actualMin, nowMin=None):
	"""On time / Delay / Advance; '' while still waiting inside the window."""
	if planMin is None:
		return ""
	if actualMin is None:
		nowMin = _nowMin() if nowMin is None else nowMin
		return "Delay" if nowMin > planMin + TOLERANCE_MIN else ""
	diff = actualMin - planMin
	if diff > TOLERANCE_MIN:
		return "Delay"
	if diff < -TOLERANCE_MIN:
		return "Advance"
	return "On time"


def modelCounts(sequence):
	seq = (sequence or "").upper()
	return dict((m, seq.count(m)) for m in MODELS)


def explode(sequence):
	"""Sequence -> {supplier: {partNo: qty}}"""
	out = {}
	for m, n in modelCounts(sequence).items():
		for partNo, q in BOM.get(m, []):
			sup = PARTS[partNo][1]
			out.setdefault(sup, {})
			out[sup][partNo] = out[sup].get(partNo, 0) + q * n
	return out


def _supplierName(code):
	for s in SUPPLIERS:
		if s["code"] == code:
			return s["name"]
	return code


# ================================================================= storage
# Both back ends return the same structures:
#   trucks : [{id, supplier, truckNo, arrivePlan, departPlan, arriveActual, departActual}]  (minutes)
#   ccr    : [{orderNo, sequence, ts}]
#   orders : [{orderNo, ccrOrderNo, supplier, status, confirmedAt, items: [{partNo, name, qty, scanned}]}]

def _state():
	g = system.util.getGlobals()
	st = g.get("receiving.sim")
	if st is None or st.get("day") != _today():
		st = _newSimState()
		g["receiving.sim"] = st
	return st


def _newSimState():
	rnd = random.Random(_today())
	now = _nowMin()
	trucks = []
	for i, (sup, no, a, d) in enumerate(TRUCK_PLAN):
		t = {"id": i + 1, "supplier": sup, "truckNo": no, "arrivePlan": _min(a), "departPlan": _min(d),
		     "arriveActual": None, "departActual": None}
		if t["arrivePlan"] + 15 < now:          # trucks that should already be here
			t["arriveActual"] = t["arrivePlan"] + rnd.choice([-8, -2, 0, 3, 9, 14])
			if t["departPlan"] + 25 < now:
				t["departActual"] = t["arriveActual"] + rnd.randint(4, 12)
		trucks.append(t)
	st = {"day": _today(), "trucks": trucks, "ccr": [], "orders": [], "seq": 0}
	_receiveCcr(st, "CCR-%s-01" % system.date.format(system.date.now(), "yyyyMMdd"), "ABCAABAABCABAABACABA")
	return st


def _loadTrucks():
	if not USE_DB:
		return _state()["trucks"]
	rows = system.dataset.toPyDataSet(system.db.runPrepQuery(
		"SELECT id, supplier, truck_no, arrive_plan, depart_plan, arrive_actual, depart_actual "
		"FROM rcv_truck_plan WHERE plan_date = ? ORDER BY supplier, arrive_plan", [_today()], DB))
	return [{"id": r["id"], "supplier": r["supplier"], "truckNo": r["truck_no"],
	         "arrivePlan": _min(r["arrive_plan"]), "departPlan": _min(r["depart_plan"]),
	         "arriveActual": _min(r["arrive_actual"]), "departActual": _min(r["depart_actual"])} for r in rows]


def _writeStamp(truck, kind, nowDate):
	if not USE_DB:
		truck[kind + "Actual"] = _min(nowDate)
		return
	col = "arrive_actual" if kind == "arrive" else "depart_actual"
	system.db.runPrepUpdate("UPDATE rcv_truck_plan SET %s = ? WHERE id = ?" % col, [nowDate, truck["id"]], DB)


def _loadCcr():
	if not USE_DB:
		return _state()["ccr"]
	rows = system.dataset.toPyDataSet(system.db.runPrepQuery(
		"SELECT order_no, sequence, received_ts FROM rcv_ccr_order "
		"WHERE received_ts >= ? ORDER BY received_ts", [system.date.midnight(system.date.now())], DB))
	return [{"orderNo": r["order_no"], "sequence": r["sequence"],
	         "ts": system.date.format(r["received_ts"], "HH:mm")} for r in rows]


def _loadOrders():
	if not USE_DB:
		return _state()["orders"]
	heads = system.dataset.toPyDataSet(system.db.runPrepQuery(
		"SELECT o.order_no, o.ccr_order_no, o.supplier, o.status, o.confirmed_ts FROM rcv_supplier_order o "
		"JOIN rcv_ccr_order c ON c.order_no = o.ccr_order_no "
		"WHERE c.received_ts >= ? ORDER BY o.order_no", [system.date.midnight(system.date.now())], DB))
	orders = []
	for h in heads:
		items = system.dataset.toPyDataSet(system.db.runPrepQuery(
			"SELECT part_no, part_name, qty, scanned_qty FROM rcv_supplier_order_item "
			"WHERE order_no = ? ORDER BY part_no", [h["order_no"]], DB))
		orders.append({"orderNo": h["order_no"], "ccrOrderNo": h["ccr_order_no"], "supplier": h["supplier"],
		               "status": h["status"],
		               "confirmedAt": system.date.format(h["confirmed_ts"], "HH:mm") if h["confirmed_ts"] else "",
		               "items": [{"partNo": i["part_no"], "name": i["part_name"], "qty": i["qty"],
		                          "scanned": i["scanned_qty"]} for i in items]})
	return orders


def _receiveCcr(st, orderNo, sequence):
	"""Sim: store a CCR order and its supplier orders."""
	sequence = (sequence or "").upper()
	st["ccr"].append({"orderNo": orderNo, "sequence": sequence,
	                  "ts": system.date.format(system.date.now(), "HH:mm")})
	for sup, parts in sorted(explode(sequence).items()):
		st["orders"].append({
			"orderNo": "%s-%s" % (orderNo, sup), "ccrOrderNo": orderNo, "supplier": sup, "status": "OPEN",
			"confirmedAt": "",
			"items": [{"partNo": p, "name": PARTS[p][0], "qty": parts[p], "scanned": 0}
			          for p in PART_ORDER if p in parts]})


def _findOrder(orderNo):
	for o in _loadOrders():
		if o["orderNo"] == orderNo:
			return o
	return None


# ================================================================= CCR orders
def receiveCcrOrder(orderNo, sequence):
	"""Entry point for CCR (gateway message handler, WebDev endpoint, tag change ...)."""
	sequence = "".join(c for c in (sequence or "").upper() if c in MODELS)
	if not sequence:
		return {"ok": False, "message": "Sequence ว่าง"}
	if not USE_DB:
		st = _state()
		if [c for c in st["ccr"] if c["orderNo"] == orderNo]:
			return {"ok": False, "message": "มีออเดอร์ %s แล้ว" % orderNo}
		_receiveCcr(st, orderNo, sequence)
	else:
		tx = system.db.beginTransaction(DB)
		try:
			now = system.date.now()
			system.db.runPrepUpdate("INSERT INTO rcv_ccr_order (order_no, sequence, received_ts, status) "
			                        "VALUES (?, ?, ?, 'DONE')", [orderNo, sequence, now], DB, tx)
			for sup, parts in sorted(explode(sequence).items()):
				so = "%s-%s" % (orderNo, sup)
				system.db.runPrepUpdate("INSERT INTO rcv_supplier_order (order_no, ccr_order_no, supplier, status, "
				                        "created_ts) VALUES (?, ?, ?, 'OPEN', ?)", [so, orderNo, sup, now], DB, tx)
				for p in PART_ORDER:
					if p in parts:
						system.db.runPrepUpdate("INSERT INTO rcv_supplier_order_item (order_no, part_no, part_name, "
						                        "qty, scanned_qty) VALUES (?, ?, ?, ?, 0)",
						                        [so, p, PARTS[p][0], parts[p]], DB, tx)
			system.db.commitTransaction(tx)
		except:
			system.db.rollbackTransaction(tx)
			raise
		finally:
			system.db.closeTransaction(tx)
	return {"ok": True, "message": "รับออเดอร์ %s (%d คัน) แล้ว" % (orderNo, len(sequence))}


def pullCcrOrders():
	"""Handheld button.  DB: process rows CCR inserted with status NEW.  Sim: new random order."""
	if USE_DB:
		rows = system.dataset.toPyDataSet(system.db.runQuery(
			"SELECT order_no, sequence FROM rcv_ccr_inbox WHERE status = 'NEW' ORDER BY order_no", DB))
		n = 0
		for r in rows:
			res = receiveCcrOrder(r["order_no"], r["sequence"])
			system.db.runPrepUpdate("UPDATE rcv_ccr_inbox SET status = ? WHERE order_no = ?",
			                        ["DONE" if res["ok"] else "ERROR", r["order_no"]], DB)
			n += 1 if res["ok"] else 0
		return {"ok": True, "message": "รับออเดอร์ใหม่จาก CCR %d รายการ" % n if n else "ไม่มีออเดอร์ใหม่จาก CCR"}
	st = _state()
	no = "CCR-%s-%02d" % (system.date.format(system.date.now(), "yyyyMMdd"), len(st["ccr"]) + 1)
	seq = "".join(random.choice("AAABBC") for _ in range(20))
	return receiveCcrOrder(no, seq)


# ================================================================= truck stamps
def stampTruck(supplier, truckNo, kind):
	"""kind 'arrive' | 'depart'.  truckNo '' / None = next truck of the supplier."""
	if not supplier:
		return {"ok": False, "message": "กรุณาเลือก Supplier"}
	trucks = [t for t in _loadTrucks() if t["supplier"] == supplier]
	if truckNo:
		trucks = [t for t in trucks if t["truckNo"] == truckNo]
	if kind == "arrive":
		cand = [t for t in trucks if t["arriveActual"] is None]
	else:
		cand = [t for t in trucks if t["arriveActual"] is not None and t["departActual"] is None]
	if not cand:
		return {"ok": False, "message": "ไม่มีรถของ %s ที่รอ%s" % (supplier, "เข้า" if kind == "arrive" else "ออก")}
	t = cand[0]
	now = system.date.now()
	_writeStamp(t, kind, now)
	plan = t["arrivePlan"] if kind == "arrive" else t["departPlan"]
	st = judge(plan, _min(now))
	return {"ok": True, "status": st,
	        "message": "%s %s %s %s  (%s)" % (supplier, t["truckNo"], "Arrive" if kind == "arrive" else "Departure",
	                                         system.date.format(now, "HH:mm"), st)}


def onPlcSignal(supplier, kind):
	"""Call from a tag change event script when the PLC reports a truck in/out."""
	return stampTruck(supplier, None, kind)


def truckRows():
	now = _nowMin()
	rows = []
	last = None
	for s in SUPPLIERS:
		group = [t for t in _loadTrucks() if t["supplier"] == s["code"]]
		group.sort(key=lambda t: t["arrivePlan"])
		for i, t in enumerate(group):
			arr = judge(t["arrivePlan"], t["arriveActual"], now)
			dep = judge(t["departPlan"], t["departActual"], now) if t["arriveActual"] is not None else ""
			status = dep or arr
			rows.append({
				"supplier": s["code"] if i == 0 else "", "pattern": s["pattern"] if i == 0 else "",
				"firstInGroup": i == 0, "truckNo": t["truckNo"],
				"arrivePlan": _hm(t["arrivePlan"]), "arriveActual": _hm(t["arriveActual"]),
				"departPlan": _hm(t["departPlan"]), "departActual": _hm(t["departActual"]),
				"arriveStatus": arr, "departStatus": dep, "status": status,
			})
	return rows


# ================================================================= handheld
def scanPart(orderNo, code):
	"""Barcode 'T0001' adds 1, 'T0001*5' adds 5."""
	code = (code or "").strip().upper()
	if not orderNo:
		return {"ok": False, "message": "กรุณาเลือกออเดอร์ก่อนสแกน"}
	if not code:
		return {"ok": False, "message": ""}
	n = 1
	if "*" in code:
		code, q = code.split("*", 1)
		try:
			n = max(1, int(q))
		except:
			return {"ok": False, "message": "จำนวนไม่ถูกต้อง: %s" % q}
	o = _findOrder(orderNo)
	if o is None:
		return {"ok": False, "message": "ไม่พบออเดอร์ %s" % orderNo}
	if o["status"] == "RECEIVED":
		return {"ok": False, "message": "ออเดอร์นี้ยืนยันรับแล้ว"}
	item = None
	for i in o["items"]:
		if i["partNo"] == code:
			item = i
	if item is None:
		return {"ok": False, "message": "%s ไม่อยู่ในออเดอร์นี้" % code}
	if item["scanned"] + n > item["qty"]:
		return {"ok": False, "message": "%s เกินจำนวน (%d/%d)" % (code, item["scanned"], item["qty"])}
	if not USE_DB:
		item["scanned"] += n
		o["status"] = "RECEIVING"
	else:
		system.db.runPrepUpdate("UPDATE rcv_supplier_order_item SET scanned_qty = scanned_qty + ? "
		                        "WHERE order_no = ? AND part_no = ?", [n, orderNo, code], DB)
		system.db.runPrepUpdate("UPDATE rcv_supplier_order SET status = 'RECEIVING' WHERE order_no = ?",
		                        [orderNo], DB)
		system.db.runPrepUpdate("INSERT INTO rcv_scan_log (ts, order_no, part_no, qty) VALUES (?, ?, ?, ?)",
		                        [system.date.now(), orderNo, code, n], DB)
	return {"ok": True, "message": "%s %s +%d  (%d/%d)" % (code, item["name"], n, item["scanned"] + (n if USE_DB else 0),
	                                                       item["qty"])}


def confirmReceive(orderNo):
	o = _findOrder(orderNo)
	if o is None:
		return {"ok": False, "message": "กรุณาเลือกออเดอร์"}
	if o["status"] == "RECEIVED":
		return {"ok": True, "message": "ยืนยันรับแล้วเมื่อ %s" % o["confirmedAt"]}
	short = [i for i in o["items"] if i["scanned"] < i["qty"]]
	if short:
		return {"ok": False, "message": "ยังสแกนไม่ครบ: " + ", ".join(
			"%s %d/%d" % (i["partNo"], i["scanned"], i["qty"]) for i in short)}
	now = system.date.now()
	if not USE_DB:
		o["status"] = "RECEIVED"
		o["confirmedAt"] = system.date.format(now, "HH:mm")
	else:
		system.db.runPrepUpdate("UPDATE rcv_supplier_order SET status = 'RECEIVED', confirmed_ts = ? "
		                        "WHERE order_no = ?", [now, orderNo], DB)
	return {"ok": True, "message": "รับสินค้าสำเร็จ %s" % orderNo}


def _orderCard(o, selected):
	qty = sum(i["qty"] for i in o["items"])
	scanned = sum(i["scanned"] for i in o["items"])
	text, color = ORDER_STATUS.get(o["status"], (o["status"], "#888888"))
	return {"orderNo": o["orderNo"], "supplier": o["supplier"], "supplierName": _supplierName(o["supplier"]),
	        "parts": len(o["items"]), "qty": qty, "scanned": scanned,
	        "statusText": text, "statusColor": color, "selected": o["orderNo"] == selected}


def getHandheld(orderNo):
	orders = _loadOrders()
	ccr = _loadCcr()
	sel = _findOrder(orderNo) if orderNo else None
	items = []
	if sel:
		for i in sel["items"]:
			items.append({"partNo": i["partNo"], "name": i["name"], "qty": i["qty"], "scanned": i["scanned"],
			              "done": i["scanned"] >= i["qty"]})
	bySupplier = []
	for s in SUPPLIERS:
		os_ = [o for o in orders if o["supplier"] == s["code"]]
		if os_:
			bySupplier.append({"supplier": s["code"], "name": s["name"],
			                   "qty": sum(sum(i["qty"] for i in o["items"]) for o in os_),
			                   "orders": len(os_)})
	text, color = ORDER_STATUS.get(sel["status"], ("", "#888888")) if sel else ("", "#888888")
	return {
		"updated": system.date.format(system.date.now(), "HH:mm:ss"),
		"ccr": ccr[-1] if ccr else {"orderNo": "-", "sequence": "", "ts": ""},
		"ccrCount": len(ccr),
		"bySupplier": bySupplier,
		"orders": [_orderCard(o, orderNo) for o in reversed(orders)],
		"selected": {
			"orderNo": sel["orderNo"] if sel else "",
			"supplier": _supplierName(sel["supplier"]) if sel else "",
			"status": sel["status"] if sel else "",
			"statusText": text, "statusColor": color,
			"confirmedAt": sel["confirmedAt"] if sel else "",
			"qty": sum(i["qty"] for i in items), "scanned": sum(i["scanned"] for i in items),
		},
		"items": items,
	}


# ================================================================= HMI / TV
def getHmi(supplier):
	trucks = [r for r in truckRows()]
	mine = []
	cur = None
	for r in trucks:
		if r["supplier"]:
			cur = r["supplier"]
		if cur == supplier:
			mine.append(r)
	return {
		"suppliers": [{"value": s["code"], "label": "%s (%s)" % (s["code"], s["pattern"])} for s in SUPPLIERS],
		"trucks": mine,
		"canArrive": len([r for r in mine if not r["arriveActual"]]) > 0,
		"canDepart": len([r for r in mine if r["arriveActual"] and not r["departActual"]]) > 0,
		"clock": system.date.format(system.date.now(), "dd/MM/yyyy HH:mm:ss"),
	}


def getMiniWms():
	orders = _loadOrders()
	ccr = _loadCcr()
	units = sum(len(c["sequence"]) for c in ccr)
	cnt = dict((k, len([o for o in orders if o["status"] == k])) for k in ORDER_STATUS)
	remaining = sum(sum(i["qty"] - i["scanned"] for i in o["items"]) for o in orders)
	models = dict((m, 0) for m in MODELS)
	for c in ccr:
		for m, n in modelCounts(c["sequence"]).items():
			models[m] += n
	mx = max(list(models.values()) + [1])
	parts = {}
	for o in orders:
		for i in o["items"]:
			p = parts.setdefault(i["partNo"], {"partNo": i["partNo"], "name": i["name"],
			                                   "supplier": o["supplier"], "qty": 0, "received": 0})
			p["qty"] += i["qty"]
			p["received"] += i["scanned"]
	partRows = []
	for k in PART_ORDER:
		if k in parts:
			p = parts[k]
			p["remain"] = p["qty"] - p["received"]
			partRows.append(p)
	return {
		"kpi": [
			{"title": "ออเดอร์จาก CCR", "value": len(ccr), "bg": "#E3F0FB", "fg": "#1F6FA8"},
			{"title": "ออเดอร์ Supplier", "value": len(orders), "bg": "#E6F6EA", "fg": "#23864A"},
			{"title": "รอรับเข้า", "value": cnt["OPEN"], "bg": "#E5F4FA", "fg": "#1C7FA6"},
			{"title": "กำลังรับเข้า", "value": cnt["RECEIVING"], "bg": "#FDF0E1", "fg": "#C26A12"},
			{"title": "แผนผลิต (คัน)", "value": units, "bg": "#E6F6EA", "fg": "#23864A"},
			{"title": "Part ค้างรับ (ชิ้น)", "value": remaining, "bg": "#FCE8E6", "fg": "#C62828"},
		],
		"orderStatus": {"open": cnt["OPEN"], "receiving": cnt["RECEIVING"], "received": cnt["RECEIVED"],
		                "total": len(orders)},
		"models": [{"name": "Model " + m, "value": models[m], "max": mx, "text": "%d คัน" % models[m]}
		           for m in MODELS],
		"sequence": ccr[-1]["sequence"] if ccr else "",
		"ccrOrderNo": ccr[-1]["orderNo"] if ccr else "-",
		"parts": partRows,
	}


def getTv():
	rows = truckRows()
	return {
		"trucks": rows,
		"summary": {
			"total": len(rows),
			"onTime": len([r for r in rows if r["status"] == "On time"]),
			"delay": len([r for r in rows if r["status"] == "Delay"]),
			"advance": len([r for r in rows if r["status"] == "Advance"]),
		},
		"wms": getMiniWms(),
		"date": system.date.format(system.date.now(), "dd/MM/yyyy"),
		"time": system.date.format(system.date.now(), "HH:mm:ss"),
	}


def resetSimulation():
	system.util.getGlobals().pop("receiving.sim", None)
