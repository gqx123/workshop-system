"""统计数据业务逻辑层"""
from datetime import datetime
from database.db import Database

db = Database()


def get_overview_stats():
    today = datetime.now().strftime("%Y-%m-%d")
    today_start = f"{today} 00:00:00"
    today_end = f"{today} 23:59:59"

    today_summary = db.execute_one(
        "SELECT "
        "    COUNT(*) AS records, "
        "    COALESCE(SUM(actual_quantity), 0) AS total_quantity, "
        "    COALESCE(SUM(defect_quantity), 0) AS total_defects "
        "FROM production_records "
        "WHERE start_time >= ? AND start_time <= ?",
        (today_start, today_end),
    )

    total_prod = db.execute_one("SELECT COUNT(*) AS cnt FROM production_records")

    pending = db.execute_one(
        "SELECT COUNT(*) AS cnt FROM fault_records WHERE status = '待处理'"
    )

    total_maint = db.execute_one("SELECT COUNT(*) AS cnt FROM maintenance_records")

    machine_today = db.execute(
        "SELECT "
        "    m.machine_code AS code, "
        "    m.machine_name AS name, "
        "    m.status AS machine_status, "
        "    COALESCE(SUM(p.actual_quantity), 0) AS quantity, "
        "    COALESCE(SUM(p.defect_quantity), 0) AS defects "
        "FROM machines m "
        "LEFT JOIN production_records p "
        "    ON m.id = p.machine_id "
        "    AND p.start_time >= ? "
        "    AND p.start_time <= ? "
        "GROUP BY m.id "
        "ORDER BY m.machine_code",
        (today_start, today_end),
    )

    insp_today = db.execute(
        "SELECT "
        "    ir.machine_id, "
        "    ir.operator_name, "
        "    ir.created_at "
        "FROM inspection_records ir "
        "WHERE ir.created_at >= ? AND ir.created_at <= ? "
        "ORDER BY ir.created_at DESC",
        (today_start, today_end),
    )

    insp_map = {}
    for rec in insp_today:
        mid = rec["machine_id"]
        if mid not in insp_map:
            insp_map[mid] = {
                "inspected": True,
                "operator": rec["operator_name"],
                "time": rec["created_at"],
            }

    machines = db.execute("SELECT id, machine_code FROM machines")
    code_to_id = {m["machine_code"]: m["id"] for m in machines}

    machine_cards = []
    for m in machine_today:
        mid = code_to_id.get(m["code"])
        insp = insp_map.get(mid, {})
        machine_cards.append({
            "code": m["code"],
            "name": m["name"],
            "machine_status": m["machine_status"],
            "quantity": m["quantity"],
            "defects": m["defects"],
            "inspected": insp.get("inspected", False),
            "insp_operator": insp.get("operator", ""),
            "insp_time": insp.get("time", ""),
        })

    return {
        "today": {
            "records": today_summary["records"] if today_summary else 0,
            "total_quantity": today_summary["total_quantity"] if today_summary else 0,
            "total_defects": today_summary["total_defects"] if today_summary else 0,
        },
        "total_production_records": total_prod["cnt"] if total_prod else 0,
        "pending_faults": pending["cnt"] if pending else 0,
        "total_maintenance_records": total_maint["cnt"] if total_maint else 0,
        "machine_today": machine_cards,
    }
