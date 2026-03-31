"""保养记录业务逻辑层"""
from database.db import Database

db = Database()


def create_maintenance(data: dict) -> int:
    """新建保养记录"""
    required = ["machine_id", "maintenance_type", "operator_name"]
    for f in required:
        if f not in data or data[f] is None:
            raise ValueError(f"缺少必填字段: {f}")

    db.execute_write(
        "INSERT INTO maintenance_records ("
        "    machine_id, maintenance_type, description, parts_replaced, "
        "    next_maintenance_date, operator_name, operator_id, duration_minutes"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            data["machine_id"],
            data["maintenance_type"],
            data.get("description", ""),
            data.get("parts_replaced", ""),
            data.get("next_maintenance_date"),
            data["operator_name"],
            data.get("operator_id", ""),
            data.get("duration_minutes", 0),
        ),
    )
    row = db.execute_one("SELECT last_insert_rowid() AS id")
    return row["id"]



def list_maintenance(
    machine_id: int | None = None,
    limit: int = 200,
) -> list[dict]:
    """查询保养记录"""
    sql = (
        "SELECT mr.*, m.machine_code, m.machine_name "
        "FROM maintenance_records mr "
        "JOIN machines m ON mr.machine_id = m.id "
        "WHERE 1=1"
    )
    params: list = []
    if machine_id is not None:
        sql += " AND mr.machine_id = ?"
        params.append(machine_id)
    sql += " ORDER BY mr.created_at DESC LIMIT ?"
    params.append(limit)
    return db.execute(sql, tuple(params))


def get_maintenance_by_id(record_id: int) -> dict | None:
    """获取单条保养记录"""
    return db.execute_one(
        "SELECT mr.*, m.machine_code, m.machine_name "
        "FROM maintenance_records mr "
        "JOIN machines m ON mr.machine_id = m.id "
        "WHERE mr.id = ?",
        (record_id,),
    )


def update_maintenance(record_id: int, data: dict) -> bool:
    """更新保养记录"""
    allowed = {
        "machine_id", "maintenance_type", "description", "parts_replaced",
        "next_maintenance_date", "operator_name", "operator_id", "duration_minutes",
    }
    updates, params = [], []
    for key, val in data.items():
        if key in allowed:
            updates.append(f"{key} = ?")
            params.append(val)
    if not updates:
        return False
    params.append(record_id)
    rows = db.execute_write(
        f"UPDATE maintenance_records SET {', '.join(updates)} WHERE id = ?", tuple(params)
    )
    return rows > 0


def delete_maintenance(record_id: int) -> bool:
    """删除保养记录"""
    rows = db.execute_write("DELETE FROM maintenance_records WHERE id = ?", (record_id,))
    return rows > 0
