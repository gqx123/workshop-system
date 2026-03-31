"""统计数据业务逻辑层"""
from datetime import datetime
from database.db import Database

db = Database()


def get_overview_stats() -> dict:
    """
    获取仪表盘概览统计数据。

    Returns:
        字典，结构如下：
        {
            "today": {
                "records":          int,  — 今日生产记录数
                "total_quantity":   int,  — 今日总产量
                "total_defects":    int,  — 今日总不良品数
            },
            "total_production_records":  int,  — 全部生产记录总数
            "pending_faults":            int,  — 待处理故障数
            "total_maintenance_records": int,  — 全部保养记录总数
            "machine_today": [                   — 今日各机床产量明细
                {
                    "code":     str,  — 机床编号
                    "name":     str,  — 机床名称
                    "quantity": int,  — 今日产量
                    "defects":  int,  — 今日不良品数
                },
                ...
            ],
        }
    """
    today = datetime.now().strftime("%Y-%m-%d")
    today_start = f"{today} 00:00:00"
    today_end = f"{today} 23:59:59"

    # ---------- 今日汇总 ----------
    today_summary = db.execute_one(
        "SELECT "
        "    COUNT(*)            AS records, "
        "    COALESCE(SUM(actual_quantity), 0) AS total_quantity, "
        "    COALESCE(SUM(defect_quantity), 0) AS total_defects "
        "FROM production_records "
        "WHERE start_time >= ? AND start_time <= ?",
        (today_start, today_end),
    )

    # ---------- 全部生产记录总数 ----------
    total_prod = db.execute_one("SELECT COUNT(*) AS cnt FROM production_records")

    # ---------- 待处理故障数 ----------
    pending = db.execute_one(
        "SELECT COUNT(*) AS cnt FROM fault_records WHERE status = '待处理'"
    )

    # ---------- 全部保养记录总数 ----------
    total_maint = db.execute_one("SELECT COUNT(*) AS cnt FROM maintenance_records")

    # ---------- 今日各机床产量明细 ----------
    machine_today = db.execute(
        "SELECT "
        "    m.machine_code  AS code, "
        "    m.machine_name  AS name, "
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

    return {
        "today": {
            "records": today_summary["records"] if today_summary else 0,
            "total_quantity": today_summary["total_quantity"] if today_summary else 0,
            "total_defects": today_summary["total_defects"] if today_summary else 0,
        },
        "total_production_records": total_prod["cnt"] if total_prod else 0,
        "pending_faults": pending["cnt"] if pending else 0,
        "total_maintenance_records": total_maint["cnt"] if total_maint else 0,
        "machine_today": machine_today,
    }
