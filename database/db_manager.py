# =============================================================================
# database/db_manager.py - Quản lý kết nối và truy vấn MySQL
# Môn: Lập Trình Mạng | Game Rắn Săn Mồi Multiplayer
# =============================================================================

import mysql.connector
from mysql.connector import pooling, Error
import hashlib
import datetime
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Quản lý toàn bộ kết nối và truy vấn CSDL MySQL.
    Sử dụng Connection Pool để tránh nghẽn cổ chai khi nhiều luồng truy cập.
    """

    def __init__(self, host="localhost", port=3306, user="root",
                 password="", database="slither_game"):
        self.db_config = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
            "charset": "utf8mb4",
            "collation": "utf8mb4_unicode_ci",
        }
        self.pool = None
        self._connect()
        self._init_schema()

    # -------------------------
    # KẾT NỐI & KHỞI TẠO SCHEMA
    # -------------------------

    def _connect(self):
        """Khởi tạo connection pool."""
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name="slither_pool",
                pool_size=10,
                **self.db_config
            )
            logger.info("✅ Kết nối MySQL thành công - Pool size: 10")
        except Error as e:
            logger.error(f"❌ Lỗi kết nối MySQL: {e}")
            self.pool = None

    def _get_conn(self):
        """Lấy kết nối từ pool."""
        if self.pool:
            return self.pool.get_connection()
        return None

    def _init_schema(self):
        """Khởi tạo bảng CSDL nếu chưa tồn tại."""
        if not self.pool:
            logger.warning("⚠️  Không có kết nối DB - bỏ qua khởi tạo schema")
            return

        sql_statements = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                username    VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(64) NOT NULL,
                display_name VARCHAR(100),
                skin_color  VARCHAR(7) DEFAULT '#4ECDC4',
                highest_score INT DEFAULT 0,
                total_kills INT DEFAULT 0,
                total_games INT DEFAULT 0,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login  DATETIME
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS match_history (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                user_id     INT NOT NULL,
                username    VARCHAR(50),
                score       INT DEFAULT 0,
                max_length  INT DEFAULT 0,
                kills       INT DEFAULT 0,
                time_alive  INT DEFAULT 0,
                played_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
            CREATE TABLE IF NOT EXISTS rooms (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                room_id     VARCHAR(20) UNIQUE NOT NULL,
                room_name   VARCHAR(100),
                host_username VARCHAR(50),
                status      ENUM('WAITING','PLAYING','CLOSED') DEFAULT 'WAITING',
                max_players INT DEFAULT 10,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        ]
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            for sql in sql_statements:
                cursor.execute(sql)
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("✅ Schema CSDL đã sẵn sàng")
        except Error as e:
            logger.error(f"❌ Lỗi khởi tạo schema: {e}")

    # -------------------------
    # XÁC THỰC TÀI KHOẢN
    # -------------------------

    @staticmethod
    def _hash_password(password: str) -> str:
        """Băm mật khẩu bằng SHA-256."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def register_user(self, username: str, password: str, display_name: str = None) -> dict:
        """
        Đăng ký tài khoản mới.
        Trả về: {"success": bool, "message": str, "user": dict | None}
        """
        if not self.pool:
            return self._mock_register(username, password, display_name)

        if not username or len(username) < 3:
            return {"success": False, "message": "Tên đăng nhập phải có ít nhất 3 ký tự"}
        if not password or len(password) < 6:
            return {"success": False, "message": "Mật khẩu phải có ít nhất 6 ký tự"}

        display_name = display_name or username
        pw_hash = self._hash_password(password)

        try:
            conn = self._get_conn()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "INSERT INTO users (username, password_hash, display_name) VALUES (%s, %s, %s)",
                (username, pw_hash, display_name)
            )
            conn.commit()
            user_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return {
                "success": True,
                "message": "Đăng ký thành công!",
                "user": {
                    "id": user_id,
                    "username": username,
                    "display_name": display_name,
                    "skin_color": "#4ECDC4",
                    "highest_score": 0
                }
            }
        except Error as e:
            if "Duplicate entry" in str(e):
                return {"success": False, "message": "Tên đăng nhập đã tồn tại!"}
            logger.error(f"Lỗi register: {e}")
            return {"success": False, "message": "Lỗi máy chủ, thử lại sau!"}

    def login_user(self, username: str, password: str) -> dict:
        """
        Đăng nhập tài khoản.
        Trả về: {"success": bool, "message": str, "user": dict | None}
        """
        if not self.pool:
            return self._mock_login(username, password)

        pw_hash = self._hash_password(password)
        try:
            conn = self._get_conn()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, username, display_name, skin_color, highest_score, total_kills, total_games "
                "FROM users WHERE username=%s AND password_hash=%s",
                (username, pw_hash)
            )
            user = cursor.fetchone()

            if user:
                # Cập nhật thời gian đăng nhập cuối
                cursor.execute(
                    "UPDATE users SET last_login=%s WHERE id=%s",
                    (datetime.datetime.now(), user["id"])
                )
                conn.commit()
                cursor.close()
                conn.close()
                return {"success": True, "message": "Đăng nhập thành công!", "user": user}
            else:
                cursor.close()
                conn.close()
                return {"success": False, "message": "Sai tên đăng nhập hoặc mật khẩu!"}
        except Error as e:
            logger.error(f"Lỗi login: {e}")
            return {"success": False, "message": "Lỗi máy chủ!"}

    # -------------------------
    # THỐNG KÊ VÀ LỊCH SỬ
    # -------------------------

    def save_match_result(self, user_id: int, username: str,
                          score: int, max_length: int, kills: int, time_alive: int):
        """Lưu kết quả ván đấu và cập nhật kỷ lục."""
        if not self.pool:
            return

        try:
            conn = self._get_conn()
            cursor = conn.cursor()

            # Ghi lịch sử
            cursor.execute(
                "INSERT INTO match_history (user_id, username, score, max_length, kills, time_alive) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, username, score, max_length, kills, time_alive)
            )

            # Cập nhật kỷ lục nếu phá được
            cursor.execute(
                "UPDATE users SET total_games = total_games + 1, total_kills = total_kills + %s, "
                "highest_score = GREATEST(highest_score, %s) WHERE id = %s",
                (kills, score, user_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"💾 Lưu kết quả {username}: score={score}, kills={kills}")
        except Error as e:
            logger.error(f"Lỗi save_match_result: {e}")

    def get_leaderboard(self, limit: int = 20) -> list:
        """Lấy bảng xếp hạng tổng (top N người chơi)."""
        if not self.pool:
            return self._mock_leaderboard()

        try:
            conn = self._get_conn()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT username, display_name, highest_score, total_kills, total_games "
                "FROM users ORDER BY highest_score DESC LIMIT %s",
                (limit,)
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Error as e:
            logger.error(f"Lỗi get_leaderboard: {e}")
            return []

    def update_skin(self, user_id: int, skin_color: str) -> bool:
        """Cập nhật màu skin của người chơi."""
        if not self.pool:
            return True  # Mock thành công

        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET skin_color=%s WHERE id=%s",
                (skin_color, user_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            logger.error(f"Lỗi update_skin: {e}")
            return False

    # -------------------------
    # MOCK DATA (khi không có MySQL)
    # -------------------------
    # Dữ liệu giả để chạy mà không cần cài MySQL

    _mock_users = {}  # username -> user_dict

    def _mock_register(self, username, password, display_name):
        if username in self._mock_users:
            return {"success": False, "message": "Tên đăng nhập đã tồn tại!"}
        user = {
            "id": len(self._mock_users) + 1,
            "username": username,
            "display_name": display_name or username,
            "skin_color": "#4ECDC4",
            "highest_score": 0,
            "_password": self._hash_password(password)
        }
        self._mock_users[username] = user
        return {"success": True, "message": "Đăng ký thành công!", "user": user}

    def _mock_login(self, username, password):
        user = self._mock_users.get(username)
        if user and user.get("_password") == self._hash_password(password):
            return {"success": True, "message": "Đăng nhập thành công!", "user": user}
        # Auto tạo tài khoản demo nếu chưa có
        if username in ("demo", "test", "player1", "player2"):
            return self._mock_register(username, password, username.capitalize())
        return {"success": False, "message": "Sai tên đăng nhập hoặc mật khẩu!"}

    def _mock_leaderboard(self):
        return [
            {"username": "ProPlayer", "display_name": "Pro Player", "highest_score": 9999, "total_kills": 50, "total_games": 30},
            {"username": "SnakeKing", "display_name": "Snake King", "highest_score": 7500, "total_kills": 40, "total_games": 25},
            {"username": "SpeedDemon", "display_name": "Speed Demon", "highest_score": 5000, "total_kills": 20, "total_games": 15},
        ]
