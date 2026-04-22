"""点检模板与点检记录业务逻辑层"""
import json
from database.db import Database

db = Database()


# ================================================================
# 点检模板 CRUD
# ================================================================

def get_templates(machine_id: int) -> list[dict]:
    """获取某台设备的所有点检模板项目"""
    return db.execute(
        "SELECT id, machine_id, item_name, item_order, created_at "
        "FROM inspection_templates "
        "WHERE machine_id = ? "
        "ORDER BY item_order, id",
        (machine_id,),
    )


def create_template(data: dict) -> int:
    """新增一个点检模板项目"""
    if not data.get("machine_id"):
        raise ValueError("缺少字段: machine_id")
    if not data.get("item_name"):
        raise ValueError("缺少字段: item_name")

    # 自动计算排序：当前最大序号 + 1
    row = db.execute_one(
        "SELECT COALESCE(MAX(item_order), 0) AS max_order "
        "FROM inspection_templates WHERE machine_id = ?",
        (data["machine_id"],),
    )
    next_order = (row["max_order"] if row else 0) + 1

    db.execute_write(
        "INSERT INTO inspection_templates (machine_id, item_name, item_order) "
        "VALUES (?, ?, ?)",
        (data["machine_id"], data["item_name"].strip(), next_order),
    )
    row = db.execute_one("SELECT last_insert_rowid() AS id")
    return row["id"]


def update_template(template_id: int, data: dict) -> bool:
    """更新点检模板项目"""
    allowed = {"item_name", "item_order"}
    updates, params = [], []
    for key, val in data.items():
        if key in allowed:
            updates.append(f"{key} = ?")
            params.append(val)
    if not updates:
        return False
    params.append(template_id)
    rows = db.execute_write(
        f"UPDATE inspection_templates SET {', '.join(updates)} WHERE id = ?",
        tuple(params),
    )
    return rows > 0


def delete_template(template_id: int) -> bool:
    """删除点检模板项目"""
    rows = db.execute_write(
        "DELETE FROM inspection_templates WHERE id = ?", (template_id,)
    )
    return rows > 0


def copy_templates(source_machine_id: int, target_machine_id: int) -> int:
    """
    将源设备的点检模板复制到目标设备。
    先清空目标设备已有模板，再复制。
    返回复制的项目数量。
    """
    if source_machine_id == target_machine_id:
        raise ValueError("源设备和目标设备不能相同")

    source_items = get_templates(source_machine_id)
    if not source_items:
        raise ValueError("源设备没有点检模板，无法复制")

    # 清空目标设备已有模板
    db.execute_write(
        "DELETE FROM inspection_templates WHERE machine_id = ?",
        (target_machine_id,),
    )

    # 批量插入
    params_list = [
        (target_machine_id, item["item_name"], item["item_order"])
        for item in source_items
    ]
    db.execute_many(
        "INSERT INTO inspection_templates (machine_id, item_name, item_order) "
        "VALUES (?, ?, ?)",
        params_list,
    )
    return len(params_list)


# ================================================================
# 点检记录 CRUD
# ================================================================

def create_inspection(data: dict) -> int:
    """提交点检记录"""
    if not data.get("machine_id"):
        raise ValueError("缺少字段: machine_id")
    if not data.get("operator_name"):
        raise ValueError("缺少字段: operator_name")

    details = data.get("details", [])
    details_json = json.dumps(details, ensure_ascii=False)

    db.execute_write(
        "INSERT INTO inspection_records (machine_id, operator_name, remark, details) "
        "VALUES (?, ?, ?, ?)",
        (data["machine_id"], data["operator_name"], data.get("remark", ""), details_json),
    )
    row = db.execute_one("SELECT last_insert_rowid() AS id")
    return row["id"]


def list_inspections(machine_id: int | None = None, limit: int = 200) -> list[dict]:
    """查询点检记录"""
    sql = (
        "SELECT ir.*, m.machine_code, m.machine_name "
        "FROM inspection_records ir "
        "JOIN machines m ON ir.machine_id = m.id "
        "WHERE 1=1"
    )
    params: list = []
    if machine_id is not None:
        sql += " AND ir.machine_id = ?"
        params.append(machine_id)
    sql += " ORDER BY ir.created_at DESC LIMIT ?"
    params.append(limit)
    rows = db.execute(sql, tuple(params))
    # 解析 details JSON
    for r in rows:
        try:
            r["details"] = json.loads(r["details"])
        except (json.JSONDecodeError, TypeError):
            r["details"] = []
    return rows


def get_inspection_by_id(record_id: int) -> dict | None:
    """获取单条点检记录"""
    row = db.execute_one(
        "SELECT ir.*, m.machine_code, m.machine_name "
        "FROM inspection_records ir "
        "JOIN machines m ON ir.machine_id = m.id "
        "WHERE ir.id = ?",
        (record_id,),
    )
    if row:
        try:
            row["details"] = json.loads(row["details"])
        except (json.JSONDecodeError, TypeError):
            row["details"] = []
    return row


def delete_inspection(record_id: int) -> bool:
    """删除点检记录"""
    rows = db.execute_write(
        "DELETE FROM inspection_records WHERE id = ?", (record_id,)
    )
    return rows > 0

def check_today_inspected(machine_id: int) -> bool:
    """检查某设备今日是否已点检"""
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    row = db.execute_one(
        "SELECT COUNT(*) AS cnt FROM inspection_records "
        "WHERE machine_id = ? AND created_at >= ? AND created_at <= ?",
        (machine_id, f"{today} 00:00:00", f"{today} 23:59:59"),
    )
    return row and row["cnt"] > 0

def import_templates(machine_id: int, items: list[str]) -> int:
    """
    批量导入点检模板（覆盖模式）。
    先清空该设备已有模板，再按顺序插入新项目。

    Args:
        machine_id: 设备 ID
        items: 点检项目名称列表

    Returns:
        导入的项目数量
    """
    if not machine_id:
        raise ValueError("缺少 machine_id")

    # 清空已有模板
    db.execute_write(
        "DELETE FROM inspection_templates WHERE machine_id = ?",
        (machine_id,),
    )

    # 过滤空行
    valid_items = [name.strip() for name in items if name.strip()]
    if not valid_items:
        raise ValueError("CSV 中没有有效的点检项目")

    # 批量插入
    params_list = [
        (machine_id, name, i + 1)
        for i, name in enumerate(valid_items)
    ]
    db.execute_many(
        "INSERT INTO inspection_templates (machine_id, item_name, item_order) "
        "VALUES (?, ?, ?)",
        params_list,
    )
    return len(params_list)
