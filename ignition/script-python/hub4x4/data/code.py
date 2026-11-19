"""
HUB 4x4 Quality Dashboard - data provider.

Called from the binding on view.custom.data of the view HUB4x4/QualityDashboard:

    hub4x4.data.getDashboard(period, start, end, point)

Set USE_DB = True and DB to your database connection name once the tables in
db/hub4x4_schema.sql exist. Until then the dashboard runs on simulated data.
"""
import random
from java.util import Date, Calendar

USE_DB = False
DB = "HUB4x4"

PERIODS = ["Hourly", "Daily", "Weekly", "Monthly"]
POINTS = ["A", "B", "C", "D", "E", "F"]
LINES = ["110A", "110B", "120A", "120B", "130A"]
ROBOTS = ["OP010", "OP050", "OP110A", "OP110B", "OP120A", "OP120B",
          "OP125B", "OP130A", "OP160C", "OP210", "OP285", "OP320"]
DEFECTS = ["Scratch", "Dimensional", "Surface Defect", "Contamination", "Damage"]
REPAIR_CAUSES = ["Repair A", "Repair B", "Repair C", "Repair D"]

# Control chart limits per inspection point: (LCL, target, UCL)
LIMITS = {
	"A": (9.50, 10.00, 10.50),
	"B": (19.40, 20.00, 20.60),
	"C": (4.80, 5.00, 5.20),
	"D": (14.70, 15.00, 15.30),
	"E": (7.85, 8.00, 8.15),
	"F": (11.75, 12.00, 12.25),
}


# ---------------------------------------------------------------- helpers
def _toDate(v):
	if v is None:
		return None
	if isinstance(v, Date):
		return v
	try:
		return Date(long(v))
	except:
		return None


def rangeFor(period):
	"""Default [start, end] for a period button."""
	cal = Calendar.getInstance()
	end = cal.getTime()
	cal.set(Calendar.HOUR_OF_DAY, 0)
	cal.set(Calendar.MINUTE, 0)
	cal.set(Calendar.SECOND, 0)
	cal.set(Calendar.MILLISECOND, 0)
	if period == "Daily":
		cal.add(Calendar.DAY_OF_MONTH, -4)
	elif period == "Weekly":
		cal.add(Calendar.WEEK_OF_YEAR, -4)
	elif period == "Monthly":
		cal.add(Calendar.MONTH, -4)
	return [cal.getTime(), end]


def applyPeriod(view, period):
	"""Used by the period buttons and the view's onStartup event."""
	r = rangeFor(period)
	view.custom.period = period
	view.custom.startDate = r[0]
	view.custom.endDate = r[1]


def _buckets(period, start, end):
	"""5 bucket [start, end, label] ending at `end`."""
	field, fmt = {
		"Hourly": (Calendar.HOUR_OF_DAY, "HH:00"),
		"Daily": (Calendar.DAY_OF_MONTH, "dd/MM"),
		"Weekly": (Calendar.WEEK_OF_YEAR, "'W'w"),
		"Monthly": (Calendar.MONTH, "MMM"),
	}.get(period, (Calendar.DAY_OF_MONTH, "dd/MM"))
	out = []
	cal = Calendar.getInstance()
	cal.setTime(end)
	for i in range(5):
		b_end = cal.getTime()
		cal.add(field, -1)
		b_start = cal.getTime()
		out.insert(0, [b_start, b_end, system.date.format(b_start, fmt)])
	return out


def perfColor(perf):
	if perf >= 97:
		return "#2DB84B"
	if perf >= 90:
		return "#F28C28"
	return "#E53935"


# ---------------------------------------------------------------- public
def getDashboard(period, start, end, point):
	period = period if period in PERIODS else "Daily"
	point = point if point in POINTS else "A"
	start = _toDate(start)
	end = _toDate(end)
	if start is None or end is None:
		start, end = rangeFor(period)
	if USE_DB:
		data = _fromDb(period, start, end, point)
	else:
		data = _simulate(period, start, end, point)
	data["updated"] = system.date.format(system.date.now(), "dd/MM/yyyy HH:mm:ss")
	return data


def getAbnormalDetail(seq):
	"""Detail record for the popup. Returns a dict (or None)."""
	if not USE_DB:
		return None
	ds = system.db.runPrepQuery(
		"SELECT ts, seq, line, point, result, process, detail "
		"FROM hub_abnormal WHERE seq = ?", [seq], DB)
	rows = _rows(ds)
	return rows[0] if rows else None


# ---------------------------------------------------------------- simulation
def _simulate(period, start, end, point):
	rnd = random.Random()
	plan = {"Hourly": 200, "Daily": 1600, "Weekly": 11200, "Monthly": 48000}[period]
	fg = int(plan * rnd.uniform(0.29, 0.33))
	ng = rnd.randint(0, max(3, fg // 150))
	repairTotal = rnd.randint(1, 4)
	repairClosed = rnd.randint(0, repairTotal)
	ok = fg - ng - repairTotal

	lcl, target, ucl = LIMITS[point]
	sd = (ucl - target) / 3.0
	warnHi = target + 2 * sd
	warnLo = target - 2 * sd
	points = []
	for i in range(30):
		v = round(rnd.gauss(target, sd * 1.1), 3)
		points.append({
			"seq": str(i + 1),
			"value": v,
			"warn": v if (v > warnHi or v < warnLo) else None,
			"ucl": ucl, "lcl": lcl, "target": target,
		})

	ngTrend = [{"bucket": b[2], "ng": rnd.randint(1, 8)} for b in _buckets(period, start, end)]
	opPerformance = [{"op": l, "ng": rnd.randint(1, 5)} for l in LINES]
	opPerformance[-1]["ng"] = rnd.randint(8, 13)

	counts = sorted([rnd.randint(2, 20) for _ in DEFECTS], reverse=True)
	tot = float(sum(counts))
	topDefects = [{"name": n, "count": c, "pct": round(c / tot * 100, 1)}
	              for n, c in zip(DEFECTS, counts)]
	repairCause = [{"name": n, "value": round(rnd.uniform(2, 5), 1)} for n in REPAIR_CAUSES]

	lines = []
	for l in LINES:
		perf = rnd.choice([98, 98, 97, 96, 99]) if l != "130A" else rnd.choice([75, 82, 91])
		lines.append({"line": l, "perf": perf, "color": perfColor(perf)})

	robots = {}
	for r in ROBOTS:
		robots[r] = rnd.choice(["RUN"] * 7 + ["IDLE", "IDLE", "ALARM"])

	abnormal = []
	now = system.date.now()
	for i in range(rnd.randint(1, 4)):
		ts = system.date.addMinutes(now, -rnd.randint(5, 600))
		res = rnd.choice(["NG", "Repair"])
		abnormal.append({
			"ts": system.date.format(ts, "dd/MM/yyyy HH:mm:ss"),
			"seq": "%03d" % rnd.randint(1, 120),
			"line": rnd.choice(LINES),
			"point": rnd.choice(POINTS),
			"result": res,
			"process": "OP" + rnd.choice(LINES),
			"detail": rnd.choice(DEFECTS),
		})
	abnormal.sort(key=lambda a: a["ts"], reverse=True)

	return {
		"kpi": {"plan": plan, "fg": fg, "ok": ok, "ng": ng,
		        "ppm": round(ng * 1000000.0 / fg, 0) if fg else 0},
		"repair": {"total": repairTotal, "closed": repairClosed,
		           "onProcess": repairTotal - repairClosed},
		"controlChart": {"point": point, "lcl": lcl, "ucl": ucl,
		                 "target": target, "points": points},
		"ngTrend": ngTrend,
		"opPerformance": opPerformance,
		"topDefects": topDefects,
		"repairCause": repairCause,
		"lines": lines,
		"robots": robots,
		"abnormal": abnormal,
	}


# ---------------------------------------------------------------- database
def _rows(ds):
	ds = system.dataset.toPyDataSet(ds)
	cols = list(ds.getColumnNames())
	return [dict(zip(cols, list(r))) for r in ds]


def _scalar(sql, args, default=0):
	v = system.db.runScalarPrepQuery(sql, args, DB)
	return default if v is None else v


def _fromDb(period, start, end, point):
	a = [start, end]
	k = _rows(system.db.runPrepQuery(
		"SELECT COALESCE(SUM(plan_qty),0) plan, COALESCE(SUM(fg_qty),0) fg, "
		"COALESCE(SUM(ok_qty),0) ok, COALESCE(SUM(ng_qty),0) ng "
		"FROM hub_production WHERE ts >= ? AND ts < ?", a, DB))[0]
	fg = float(k["fg"] or 0)
	kpi = {"plan": k["plan"], "fg": k["fg"], "ok": k["ok"], "ng": k["ng"],
	       "ppm": round(k["ng"] * 1000000.0 / fg, 0) if fg else 0}

	total = _scalar("SELECT COUNT(*) FROM hub_repair WHERE ts >= ? AND ts < ?", a)
	closed = _scalar("SELECT COUNT(*) FROM hub_repair WHERE ts >= ? AND ts < ? AND status = 'CLOSED'", a)

	lcl, target, ucl = LIMITS[point]
	insp = _rows(system.db.runPrepQuery(
		"SELECT seq, value, lcl, ucl, target FROM hub_inspection "
		"WHERE point = ? AND ts >= ? AND ts < ? ORDER BY ts", [point, start, end], DB))[-30:]
	points = []
	for r in insp:
		lcl, ucl, target = r["lcl"], r["ucl"], r["target"]
		sd = (ucl - target) / 3.0
		v = r["value"]
		points.append({"seq": str(r["seq"]), "value": v, "lcl": lcl, "ucl": ucl, "target": target,
		               "warn": v if abs(v - target) > 2 * sd else None})

	ngTrend = []
	for b in _buckets(period, start, end):
		ngTrend.append({"bucket": b[2], "ng": _scalar(
			"SELECT COALESCE(SUM(ng_qty),0) FROM hub_production WHERE ts >= ? AND ts < ?", [b[0], b[1]])})

	opPerformance = [{"op": r["line"], "ng": r["ng"]} for r in _rows(system.db.runPrepQuery(
		"SELECT line, COALESCE(SUM(ng_qty),0) ng FROM hub_production "
		"WHERE ts >= ? AND ts < ? GROUP BY line ORDER BY line", a, DB))]

	d = _rows(system.db.runPrepQuery(
		"SELECT defect_type name, COUNT(*) cnt FROM hub_abnormal "
		"WHERE ts >= ? AND ts < ? GROUP BY defect_type ORDER BY COUNT(*) DESC", a, DB))[:5]
	tot = float(sum([r["cnt"] for r in d])) or 1.0
	topDefects = [{"name": r["name"], "count": r["cnt"], "pct": round(r["cnt"] / tot * 100, 1)} for r in d]

	repairCause = [{"name": r["cause"], "value": r["cnt"]} for r in _rows(system.db.runPrepQuery(
		"SELECT cause, COUNT(*) cnt FROM hub_repair WHERE ts >= ? AND ts < ? GROUP BY cause ORDER BY cause", a, DB))]

	lines = [{"line": r["line"], "perf": r["performance"], "color": perfColor(r["performance"])}
	         for r in _rows(system.db.runQuery("SELECT line, performance FROM hub_line_status ORDER BY line", DB))]

	robots = dict([(r["robot"], r["status"]) for r in _rows(
		system.db.runQuery("SELECT robot, status FROM hub_robot_status", DB))])

	abnormal = []
	for r in _rows(system.db.runPrepQuery(
			"SELECT ts, seq, line, point, result, process, defect_type FROM hub_abnormal "
			"WHERE ts >= ? AND ts < ? ORDER BY ts DESC", a, DB))[:20]:
		abnormal.append({"ts": system.date.format(r["ts"], "dd/MM/yyyy HH:mm:ss"), "seq": str(r["seq"]),
		                 "line": r["line"], "point": r["point"], "result": r["result"],
		                 "process": r["process"], "detail": r["defect_type"]})

	return {
		"kpi": kpi,
		"repair": {"total": total, "closed": closed, "onProcess": total - closed},
		"controlChart": {"point": point, "lcl": lcl, "ucl": ucl, "target": target, "points": points},
		"ngTrend": ngTrend, "opPerformance": opPerformance, "topDefects": topDefects,
		"repairCause": repairCause, "lines": lines, "robots": robots, "abnormal": abnormal,
	}
