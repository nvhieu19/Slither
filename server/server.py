# =============================================================================
# server/server.py - Game Server chính (đa luồng TCP)
# Môn: Lập Trình Mạng | Game Rắn Săn Mồi Multiplayer
# =============================================================================

import socket
import threading
import time
import uuid
import logging
import sys
import os

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.protocol import PacketType, encode_packet, PacketReader, GameConfig
from server.game_logic import GameRoom
from database.db_manager import DatabaseManager

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("SERVER")


class ClientHandler(threading.Thread):
    """
    Luồng xử lý kết nối cho 1 Client.
    Mỗi client kết nối sẽ có 1 ClientHandler riêng.
    """

    def __init__(self, conn: socket.socket, addr, server: "GameServer"):
        super().__init__(daemon=True)
        self.conn = conn
        self.addr = addr
        self.server = server
        self.reader = PacketReader(conn)

        # Thông tin người chơi (sau khi đăng nhập)
        self.player_id = str(uuid.uuid4())[:8]
        self.username = None
        self.display_name = None
        self.skin_color = "#4ECDC4"
        self.user_db_id = None
        self.authenticated = False

        # Phòng hiện tại
        self.current_room_id: str | None = None

        self.running = True
        logger.info(f"🔗 Client kết nối: {addr} | ID={self.player_id}")

    # -------------------------
    # VÒNG LẶP NHẬN GÓI TIN
    # -------------------------

    def run(self):
        """Luồng đọc gói tin từ client liên tục."""
        try:
            while self.running:
                packet = self.reader.read_packet()
                if packet is None:
                    break
                self._handle_packet(packet)
        except Exception as e:
            logger.debug(f"Lỗi recv từ {self.addr}: {e}")
        finally:
            self._cleanup()

    def _handle_packet(self, packet: dict):
        """Điều phối xử lý gói tin theo type."""
        ptype = packet.get("type")
        payload = packet.get("payload", {})

        handlers = {
            PacketType.LOGIN_REQ:       self._handle_login,
            PacketType.REGISTER_REQ:    self._handle_register,
            PacketType.ROOM_LIST_REQ:   self._handle_room_list,
            PacketType.CREATE_ROOM_REQ: self._handle_create_room,
            PacketType.JOIN_ROOM_REQ:   self._handle_join_room,
            PacketType.LEAVE_ROOM_REQ:  self._handle_leave_room,
            PacketType.START_GAME_REQ:  self._handle_start_game,
            PacketType.PLAYER_INPUT:    self._handle_player_input,
            PacketType.CHAT_MSG:        self._handle_chat,
            PacketType.RESPAWN_REQ:     self._handle_respawn,
            PacketType.UPDATE_SKIN_REQ: self._handle_update_skin,
            PacketType.LEADERBOARD_REQ: self._handle_leaderboard,
            PacketType.DISCONNECT:      self._handle_disconnect_req,
        }
        handler = handlers.get(ptype)
        if handler:
            handler(payload)
        else:
            logger.debug(f"Gói tin không xác định: {ptype}")

    # -------------------------
    # XỬ LÝ XÁC THỰC
    # -------------------------

    def _handle_login(self, payload: dict):
        username = payload.get("username", "").strip()
        password = payload.get("password", "")
        result = self.server.db.login_user(username, password)

        if result["success"]:
            user = result["user"]
            self.username = user["username"]
            self.display_name = user.get("display_name", username)
            self.skin_color = user.get("skin_color", "#4ECDC4")
            self.user_db_id = user.get("id")
            self.authenticated = True
            # Đăng ký handler vào server
            self.server.clients[self.player_id] = self

        self.send(PacketType.LOGIN_RES, {
            "success": result["success"],
            "message": result["message"],
            "player_id": self.player_id if result["success"] else None,
            "user": result.get("user") if result["success"] else None
        })
        if result["success"]:
            logger.info(f"✅ Đăng nhập: {self.username} ({self.addr})")

    def _handle_register(self, payload: dict):
        username = payload.get("username", "").strip()
        password = payload.get("password", "")
        display_name = payload.get("display_name", username)
        result = self.server.db.register_user(username, password, display_name)

        self.send(PacketType.REGISTER_RES, {
            "success": result["success"],
            "message": result["message"]
        })

    # -------------------------
    # XỬ LÝ PHÒNG
    # -------------------------

    def _handle_room_list(self, payload: dict):
        rooms = [r.get_room_info() for r in self.server.rooms.values()
                 if r.status != "CLOSED"]
        self.send(PacketType.ROOM_LIST_RES, {"rooms": rooms})

    def _handle_create_room(self, payload: dict):
        if not self.authenticated:
            return self.send_error("Chưa đăng nhập!")

        room_name = payload.get("room_name", f"Phòng của {self.display_name}")[:50]
        max_players = min(int(payload.get("max_players", 10)), GameConfig.MAX_ROOM_PLAYERS)

        room_id = f"R{uuid.uuid4().hex[:6].upper()}"
        room = GameRoom(room_id, room_name, self.username, max_players)
        self.server.rooms[room_id] = room

        # Thêm người tạo vào phòng ngay
        room.add_player(self.player_id, self.username, self.display_name, self.skin_color)
        self.current_room_id = room_id

        self.send(PacketType.CREATE_ROOM_RES, {
            "success": True,
            "room_id": room_id,
            "room_info": room.get_room_info(),
            "player_list": room.get_player_list()
        })
        logger.info(f"🏠 Tạo phòng: {room_name} ({room_id}) bởi {self.username}")

    def _handle_join_room(self, payload: dict):
        if not self.authenticated:
            return self.send_error("Chưa đăng nhập!")

        room_id = payload.get("room_id")
        room = self.server.rooms.get(room_id)

        if not room:
            return self.send(PacketType.JOIN_ROOM_RES, {"success": False, "message": "Phòng không tồn tại!"})
        if room.status == "PLAYING":
            return self.send(PacketType.JOIN_ROOM_RES, {"success": False, "message": "Game đang diễn ra!"})
        if len(room.snakes) >= room.max_players:
            return self.send(PacketType.JOIN_ROOM_RES, {"success": False, "message": "Phòng đã đầy!"})

        # Rời phòng cũ nếu có
        if self.current_room_id:
            self._leave_current_room()

        room.add_player(self.player_id, self.username, self.display_name, self.skin_color)
        self.current_room_id = room_id

        self.send(PacketType.JOIN_ROOM_RES, {
            "success": True,
            "room_id": room_id,
            "room_info": room.get_room_info(),
            "player_list": room.get_player_list()
        })

        # Thông báo cho mọi người trong phòng
        self._broadcast_room_update(room)
        logger.info(f"🚪 {self.username} vào phòng {room_id}")

    def _handle_leave_room(self, payload: dict):
        self._leave_current_room()
        self.send(PacketType.LEAVE_ROOM_REQ, {"success": True})

    def _leave_current_room(self):
        if not self.current_room_id:
            return
        room = self.server.rooms.get(self.current_room_id)
        if room:
            # Lưu thống kê nếu đã đăng nhập và game đã chạy
            snake = room.snakes.get(self.player_id)
            if snake and self.user_db_id:
                self.server.db.save_match_result(
                    self.user_db_id, self.username,
                    snake.score, snake.max_length, snake.kills,
                    int(time.time() - snake.start_time) if room.game_start_time else 0
                )
            room.remove_player(self.player_id)
            self._broadcast_room_update(room)

            # Dọn phòng trống
            if len(room.snakes) == 0:
                room.status = "CLOSED"
                logger.info(f"🗑️  Phòng {self.current_room_id} đóng cửa (trống)")

        self.current_room_id = None

    def _handle_start_game(self, payload: dict):
        room = self.server.rooms.get(self.current_room_id)
        if not room:
            return
        if room.host_username != self.username:
            return self.send_error("Chỉ host mới có thể bắt đầu!")
        if len(room.snakes) < GameConfig.MIN_START_PLAYERS:
            return self.send_error("Cần ít nhất 1 người chơi!")
        if room.status == "PLAYING":
            return

        room.status = "PLAYING"
        room.game_start_time = time.time()

        # Gửi GAME_START cho tất cả
        self._broadcast_to_room(room, PacketType.GAME_START, {
            "room_id": room.room_id,
            "world_width": GameConfig.WORLD_WIDTH,
            "world_height": GameConfig.WORLD_HEIGHT,
        })

        # Khởi chạy game loop cho phòng này
        loop_thread = threading.Thread(
            target=self.server.run_game_loop,
            args=(room,),
            daemon=True
        )
        loop_thread.start()
        logger.info(f"🎮 Game bắt đầu trong phòng {self.current_room_id}")

    # -------------------------
    # XỬ LÝ GAMEPLAY
    # -------------------------

    def _handle_player_input(self, payload: dict):
        room = self.server.rooms.get(self.current_room_id)
        if not room or room.status != "PLAYING":
            return
        angle = float(payload.get("angle", 0))
        is_boosting = bool(payload.get("is_boosting", False))
        room.process_input(self.player_id, angle, is_boosting)

    def _handle_chat(self, payload: dict):
        room = self.server.rooms.get(self.current_room_id)
        if not room:
            return
        message = str(payload.get("message", ""))[:200]
        self._broadcast_to_room(room, PacketType.CHAT_BROADCAST, {
            "sender": self.display_name,
            "message": message,
            "timestamp": time.time()
        })

    def _handle_respawn(self, payload: dict):
        room = self.server.rooms.get(self.current_room_id)
        if not room or room.status != "PLAYING":
            return
        # Tạo lại rắn cho người chơi
        from server.game_logic import Snake
        snake = Snake(self.player_id, self.username, self.display_name, self.skin_color)
        room.snakes[self.player_id] = snake
        logger.info(f"♻️  {self.username} hồi sinh")

    def _handle_update_skin(self, payload: dict):
        skin_color = payload.get("skin_color", "#4ECDC4")
        # Validate HEX color
        if not (skin_color.startswith("#") and len(skin_color) == 7):
            return self.send_error("Màu sắc không hợp lệ!")

        self.skin_color = skin_color
        success = False
        if self.user_db_id:
            success = self.server.db.update_skin(self.user_db_id, skin_color)
        else:
            success = True  # mock mode

        # Cập nhật skin trong game nếu đang chơi
        room = self.server.rooms.get(self.current_room_id)
        if room and self.player_id in room.snakes:
            room.snakes[self.player_id].skin_color = skin_color

        self.send(PacketType.UPDATE_SKIN_RES, {"success": success, "skin_color": skin_color})

    def _handle_leaderboard(self, payload: dict):
        data = self.server.db.get_leaderboard(20)
        self.send(PacketType.LEADERBOARD_RES, {"leaderboard": data})

    def _handle_disconnect_req(self, payload: dict):
        self.running = False

    # -------------------------
    # TIỆN ÍCH
    # -------------------------

    def send(self, packet_type: str, payload: dict):
        """Gửi gói tin tới client."""
        try:
            data = encode_packet(packet_type, payload)
            self.conn.sendall(data)
        except Exception:
            self.running = False

    def send_error(self, message: str):
        self.send(PacketType.ERROR_MSG, {"message": message})

    def _broadcast_to_room(self, room: GameRoom, packet_type: str, payload: dict):
        """Broadcast gói tin tới tất cả client trong phòng."""
        data = encode_packet(packet_type, payload)
        for pid in list(room.snakes.keys()):
            handler = self.server.clients.get(pid)
            if handler:
                try:
                    handler.conn.sendall(data)
                except Exception:
                    pass

    def _broadcast_room_update(self, room: GameRoom):
        """Broadcast cập nhật danh sách người trong phòng."""
        self._broadcast_to_room(room, PacketType.ROOM_UPDATE, {
            "room_info": room.get_room_info(),
            "player_list": room.get_player_list()
        })

    def _cleanup(self):
        """Dọn dẹp khi client ngắt kết nối."""
        logger.info(f"❌ Client ngắt kết nối: {self.username or self.addr}")
        self._leave_current_room()
        self.server.clients.pop(self.player_id, None)
        try:
            self.conn.close()
        except Exception:
            pass


# =============================================================================
# GAME SERVER CHÍNH
# =============================================================================

class GameServer:
    """
    Server game chính.
    - Lắng nghe kết nối TCP mới
    - Quản lý danh sách clients và rooms
    - Chạy game loop cho từng phòng
    """

    def __init__(self, host: str = GameConfig.SERVER_HOST,
                 port: int = GameConfig.SERVER_PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False

        # Quản lý clients và rooms
        self.clients: dict[str, ClientHandler] = {}   # player_id -> handler
        self.rooms: dict[str, GameRoom] = {}           # room_id -> GameRoom

        # Kết nối CSDL
        self.db = DatabaseManager()

        logger.info(f"🐍 Slither.io Server v1.0 khởi động...")
        logger.info(f"📡 Host: {host}:{port}")

    def start(self):
        """Khởi chạy server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(50)
        self.running = True

        logger.info(f"✅ Server đang lắng nghe tại {self.host}:{self.port}")
        logger.info("=" * 60)

        try:
            while self.running:
                try:
                    conn, addr = self.server_socket.accept()
                    conn.settimeout(GameConfig.SOCKET_TIMEOUT)
                    handler = ClientHandler(conn, addr, self)
                    handler.start()
                except OSError:
                    break
        except KeyboardInterrupt:
            logger.info("🛑 Server dừng do người dùng yêu cầu")
        finally:
            self.stop()

    def stop(self):
        """Dừng server."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        logger.info("Server đã dừng.")

    def run_game_loop(self, room: GameRoom):
        """
        Vòng lặp game cho 1 phòng.
        Chạy ở tickrate cố định = SERVER_TICKRATE.
        """
        tick_interval = 1.0 / GameConfig.SERVER_TICKRATE
        logger.info(f"⚙️  Game loop bắt đầu: phòng {room.room_id}")

        while room.status == "PLAYING":
            t_start = time.monotonic()

            # Tick logic
            events = room.tick()

            # Xử lý sự kiện
            for event in events:
                if event["type"] == "PLAYER_DEAD":
                    self._handle_player_death(room, event)

            # Kiểm tra phòng có người không
            alive_count = sum(1 for s in room.snakes.values() if s.alive)
            total_count = len(room.snakes)
            if total_count == 0:
                room.status = "CLOSED"
                break

            # Broadcast world state tới tất cả clients trong phòng
            for pid in list(room.snakes.keys()):
                handler = self.clients.get(pid)
                if not handler:
                    continue
                try:
                    world_state = room.get_world_state(viewer_id=pid)
                    data = encode_packet(PacketType.WORLD_STATE, world_state)
                    handler.conn.sendall(data)
                except Exception:
                    pass

            # Điều chỉnh tốc độ tick
            elapsed = time.monotonic() - t_start
            sleep_time = tick_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        logger.info(f"⚙️  Game loop kết thúc: phòng {room.room_id}")

    def _handle_player_death(self, room: GameRoom, event: dict):
        """Gửi thông báo chết cho client liên quan."""
        dead_pid = event["player_id"]
        handler = self.clients.get(dead_pid)
        if handler:
            handler.send(PacketType.PLAYER_DEAD, event)

        # Lưu vào CSDL
        if handler and handler.user_db_id:
            self.db.save_match_result(
                handler.user_db_id,
                event["username"],
                event["score"],
                event["max_length"],
                event["kills"],
                event["time_alive"]
            )

        # Broadcast cho phòng
        killer_pid = event.get("killer_id")
        if killer_pid:
            killer_handler = self.clients.get(killer_pid)
            killer_name = killer_handler.display_name if killer_handler else "Unknown"
        else:
            killer_name = "Tường biên"

        for pid in list(room.snakes.keys()):
            h = self.clients.get(pid)
            if h and pid != dead_pid:
                h.send(PacketType.CHAT_BROADCAST, {
                    "sender": "🎮 System",
                    "message": f"💀 {event['username']} bị {killer_name} tiêu diệt! Score: {event['score']}",
                    "timestamp": time.time()
                })


# -------------------------
# ENTRY POINT
# -------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Slither.io Game Server")
    parser.add_argument("--host", default=GameConfig.SERVER_HOST)
    parser.add_argument("--port", type=int, default=GameConfig.SERVER_PORT)
    args = parser.parse_args()

    server = GameServer(args.host, args.port)
    server.start()
