"""数据库操作封装 - 统一管理 SQLite 连接与基础 CRUD"""
import sqlite3
import logging
from config import DB_PATH
from database.schema import SCHEMA

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """数据库操作异常"""
    pass


class Database:
    """
    数据库操作类，封装所有 SQLite 交互。

    使用方式:
        db = Database()
        db.init_db()
        db.seed_machines()

        rows = db.execute("SELECT * FROM machines")
        row  = db.execute_one("SELECT * FROM machines WHERE id = ?", (1,))
        new_id = db.execute_write("INSERT INTO machines (machine_code, machine_name) VALUES (?, ?)",
                                  ("MC-006", "新机床"))
    """

    # ----------------------------------------------------------------
    # 连接
    # ----------------------------------------------------------------

    def get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接。

        Returns:
            配置好的 sqlite3.Connection（Row 模式，WAL 日志，外键约束开启）

        Raises:
            DatabaseError: 连接失败时抛出
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA busy_timeout=5000")  # 锁等待 5 秒
            return conn
        except sqlite3.Error as e:
            logger.error("数据库连接失败: %s", e)
            raise DatabaseError(f"数据库连接失败: {e}") from e

    # ----------------------------------------------------------------
    # 查询
    # ----------------------------------------------------------------

    def execute(self, sql: str, params: tuple = ()) -> list[dict]:
        """
        执行查询语句，返回字典列表。

        Args:
            sql:    SQL 查询语句
            params: 参数元组

        Returns:
            查询结果列表，每条记录为 dict

        Raises:
            DatabaseError: SQL 执行失败时抛出
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error("查询失败 [%s] params=%s: %s", sql, params, e)
            raise DatabaseError(f"查询失败: {e}") from e
        finally:
            conn.close()

    def execute_one(self, sql: str, params: tuple = ()) -> dict | None:
        """
        执行查询语句，返回单条字典或 None。

        Args:
            sql:    SQL 查询语句
            params: 参数元组

        Returns:
            单条记录 dict，无结果时返回 None

        Raises:
            DatabaseError: SQL 执行失败时抛出
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(sql, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error("查询失败 [%s] params=%s: %s", sql, params, e)
            raise DatabaseError(f"查询失败: {e}") from e
        finally:
            conn.close()

    # ----------------------------------------------------------------
    # 写入
    # ----------------------------------------------------------------

    def execute_write(self, sql: str, params: tuple = ()) -> int:
        """
        执行写入 / 更新 / 删除语句。

        Args:
            sql:    SQL 写入语句
            params: 参数元组

        Returns:
            受影响的行数（INSERT=1, UPDATE/DELETE=实际行数）

        Raises:
            DatabaseError: SQL 执行失败时抛出
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            conn.rollback()
            logger.error("写入失败 [%s] params=%s: %s", sql, params, e)
            raise DatabaseError(f"写入失败: {e}") from e
        finally:
            conn.close()


    def execute_many(self, sql: str, params_list: list[tuple]) -> int:
        """
        批量执行写入语句。

        Args:
            sql:        SQL 写入语句（参数化）
            params_list: 参数列表

        Returns:
            受影响的行数

        Raises:
            DatabaseError: SQL 执行失败时抛出
        """
        conn = self.get_connection()
        try:
            cursor = conn.executemany(sql, params_list)
            conn.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            conn.rollback()
            logger.error("批量写入失败 [%s]: %s", sql, e)
            raise DatabaseError(f"批量写入失败: {e}") from e
        finally:
            conn.close()

    # ----------------------------------------------------------------
    # 事务
    # ----------------------------------------------------------------

    def execute_transaction(self, operations: list[tuple]) -> None:
        """
        在同一事务中执行多条写入操作，全部成功才提交，任一失败则全部回滚。

        Args:
            operations: 列表，每项为 (sql, params) 二元组

        Raises:
            DatabaseError: 任一操作失败时回滚并抛出
        """
        conn = self.get_connection()
        try:
            for sql, params in operations:
                conn.execute(sql, params)
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error("事务执行失败，已回滚: %s", e)
            raise DatabaseError(f"事务执行失败: {e}") from e
        finally:
            conn.close()

    # ----------------------------------------------------------------
    # 初始化
    # ----------------------------------------------------------------

    def init_db(self) -> None:
        """
        根据 schema.py 中的 SCHEMA 建表（幂等，重复调用不会出错）。

        同时创建索引以加速常见查询。

        Raises:
            DatabaseError: 建表失败时抛出
        """
        conn = self.get_connection()
        try:
            conn.executescript(SCHEMA)
            conn.commit()
            logger.info("数据库表初始化完成")
        except sqlite3.Error as e:
            logger.error("数据库初始化失败: %s", e)
            raise DatabaseError(f"数据库初始化失败: {e}") from e
        finally:
            conn.close()

    def seed_machines(self) -> None:
        """
        如果 machines 表为空，插入 config.py 中的预置机床数据。

        Raises:
            DatabaseError: 插入失败时抛出
        """
        count_row = self.execute_one("SELECT COUNT(*) AS cnt FROM machines")
        if count_row and count_row["cnt"] > 0:
            logger.info("machines 表已有 %d 条记录，跳过预置", count_row["cnt"])
            return

        from config import DEFAULT_MACHINES
        if not DEFAULT_MACHINES:
            logger.warning("DEFAULT_MACHINES 为空，无预置数据")
            return

        conn = self.get_connection()
        try:
            conn.executemany(
                "INSERT INTO machines (machine_code, machine_name, machine_type, location) "
                "VALUES (?, ?, ?, ?)",
                DEFAULT_MACHINES,
            )
            conn.commit()
            logger.info("预置 %d 台机床数据完成", len(DEFAULT_MACHINES))
        except sqlite3.Error as e:
            conn.rollback()
            logger.error("预置机床数据失败: %s", e)
            raise DatabaseError(f"预置机床数据失败: {e}") from e
        finally:
            conn.close()

    # ----------------------------------------------------------------
    # 辅助方法
    # ----------------------------------------------------------------

    def table_exists(self, table_name: str) -> bool:
        """检查指定表是否存在"""
        row = self.execute_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        return row is not None

    def get_table_row_count(self, table_name: str) -> int:
        """获取指定表的总行数"""
        row = self.execute_one(f"SELECT COUNT(*) AS cnt FROM {table_name}")
        return row["cnt"] if row else 0

    def vacuum(self) -> None:
        """压缩数据库文件（清理已删除数据的空间）"""
        conn = self.get_connection()
        try:
            conn.execute("VACUUM")
        except sqlite3.Error as e:
            logger.error("VACUUM 失败: %s", e)
        finally:
            conn.close()
