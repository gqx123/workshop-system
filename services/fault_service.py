"""故障记录业务逻辑层"""
from datetime import datetime
from database.db import Database

db = Database()


def create_fault(data: dict) -> int:
    """新建故障记录"""
    required = ["machine_id", "operator_name"]
    for f in required:
        if f not in data or data[f] is None:
            raise ValueError(f"缺少必填字段: {f}")

    db.execute_write(
        "INSERT INTO fault_records ("
        "    machine_id, fault_type, description, severity, "
        "    status, operator_name"
        ") VALUES (?, ?, ?, ?, '待处理', ?)",
        (
            data["machine_id"],
            data.get("fault_type", ""),
            data.get("description", ""),
            data.get("severity", "一般"),
            data["operator_name"],
        ),
    )
    row = db.execute_one("SELECT last_insert_rowid() AS id")
    return row["id"]



def list_faults(
    status: str | None = None,
    limit: int = 200,
) -> list[dict]:
    """查询故障记录"""
    sql = (
        "SELECT fr.*, m.machine_code, m.machine_name "
        "FROM fault_records fr "
        "JOIN machines m ON fr.machine_id = m.id "
        "WHERE 1=1"
    )
    params: list = []
    if status is not None:
        sql += " AND fr.status = ?"
        params.append(status)
    sql += " ORDER BY fr.created_at DESC LIMIT ?"
    params.append(limit)
    return db.execute(sql, tuple(params))


def get_fault_by_id(fault_id: int) -> dict | None:
    """获取单条故障记录"""
    return db.execute_one(
        "SELECT fr.*, m.machine_code, m.machine_name "
        "FROM fault_records fr "
        "JOIN machines m ON fr.machine_id = m.id "
        "WHERE fr.id = ?",
        (fault_id,),
    )


def update_fault(fault_id: int, data: dict) -> bool:
    """更新故障记录"""
    allowed = {
        "machine_id", "fault_type", "description", "severity",
        "status", "operator_name", "resolution", "resolved_at",
    }
    updates, params = [], []
    for key, val in data.items():
        if key in allowed:
            updates.append(f"{key} = ?")
            params.append(val)
    if not updates:
        return False
    params.append(fault_id)
    rows = db.execute_write(
        f"UPDATE fault_records SET {', '.join(updates)} WHERE id = ?", tuple(params)
    )
    return rows > 0


def resolve_fault(fault_id: int, resolution: str) -> bool:
    """标记故障已解决"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = db.execute_write(
        "UPDATE fault_records SET status = '已解决', resolution = ?, resolved_at = ? "
        "WHERE id = ?",
        (resolution, now, fault_id),
    )
    return rows > 0


def delete_fault(fault_id: int) -> bool:
    """删除故障记录"""
    rows = db.execute_write("DELETE FROM fault_records WHERE id = ?", (fault_id,))
    return rows > 0
