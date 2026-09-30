# =============================================================================
# shared/protocol.py - Định nghĩa giao thức truyền thông Client-Server
# Môn: Lập Trình Mạng | Game Rắn Săn Mồi Multiplayer
# =============================================================================

import json
import struct

# -------------------------
# LOẠI GÓI TIN (PACKET TYPE)
# -------------------------
class PacketType:
    # Client -> Server
    LOGIN_REQ       = "LOGIN_REQ"       # Yêu cầu đăng nhập
    REGISTER_REQ    = "REGISTER_REQ"    # Yêu cầu đăng ký
    ROOM_LIST_REQ   = "ROOM_LIST_REQ"   # Yêu cầu danh sách phòng
    CREATE_ROOM_REQ = "CREATE_ROOM_REQ" # Yêu cầu tạo phòng
    JOIN_ROOM_REQ   = "JOIN_ROOM_REQ"   # Yêu cầu vào phòng
    LEAVE_ROOM_REQ  = "LEAVE_ROOM_REQ"  # Yêu cầu rời phòng
    START_GAME_REQ  = "START_GAME_REQ"  # Yêu cầu bắt đầu game (Host)
    PLAYER_INPUT    = "PLAYER_INPUT"    # Gửi input điều khiển (góc + boost)
    CHAT_MSG        = "CHAT_MSG"        # Gửi tin nhắn chat
    RESPAWN_REQ     = "RESPAWN_REQ"     # Yêu cầu hồi sinh
    UPDATE_SKIN_REQ = "UPDATE_SKIN_REQ" # Yêu cầu cập nhật skin
    LEADERBOARD_REQ = "LEADERBOARD_REQ" # Yêu cầu bảng xếp hạng tổng
    DISCONNECT      = "DISCONNECT"      # Ngắt kết nối tình nguyện

    # Server -> Client
    LOGIN_RES       = "LOGIN_RES"       # Phản hồi đăng nhập
    REGISTER_RES    = "REGISTER_RES"    # Phản hồi đăng ký
    ROOM_LIST_RES   = "ROOM_LIST_RES"   # Danh sách phòng
    CREATE_ROOM_RES = "CREATE_ROOM_RES" # Kết quả tạo phòng
    JOIN_ROOM_RES   = "JOIN_ROOM_RES"   # Kết quả vào phòng
    ROOM_UPDATE     = "ROOM_UPDATE"     # Cập nhật danh sách trong phòng
    GAME_START      = "GAME_START"      # Thông báo game bắt đầu
    WORLD_STATE     = "WORLD_STATE"     # Trạng thái thế giới game
    PLAYER_DEAD     = "PLAYER_DEAD"     # Thông báo rắn chết
    CHAT_BROADCAST  = "CHAT_BROADCAST"  # Broadcast tin nhắn
    ERROR_MSG       = "ERROR_MSG"       # Thông báo lỗi
    LEADERBOARD_RES = "LEADERBOARD_RES" # Bảng xếp hạng tổng
    UPDATE_SKIN_RES = "UPDATE_SKIN_RES" # Kết quả cập nhật skin


# -------------------------
# HÀM ĐÓNG GÓI / GIẢI GÓI
# -------------------------

def encode_packet(packet_type: str, payload: dict) -> bytes:
    """
    Đóng gói dữ liệu thành bytes để gửi qua TCP.
    Định dạng: [4 bytes độ dài JSON] + [JSON bytes]
    """
    message = {
        "type": packet_type,
        "payload": payload
    }
    json_bytes = json.dumps(message, ensure_ascii=False).encode("utf-8")
    # Thêm header 4 bytes chứa độ dài để xử lý sticky packets TCP
    header = struct.pack(">I", len(json_bytes))
    return header + json_bytes


def decode_packet(data: bytes) -> dict | None:
    """
    Giải mã bytes thành dict.
    Trả về None nếu dữ liệu không hợp lệ.
    """
    try:
        return json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


# -------------------------
# CLASS ĐỌC GÓI TIN TCP
# -------------------------

class PacketReader:
    """
    Xử lý việc đọc gói tin TCP đủ bytes (giải quyết sticky packet).
    Sử dụng buffer để tích lũy dữ liệu nhận được theo từng chunk.
    """

    def __init__(self, sock):
        self.sock = sock
        self.buffer = b""

    def read_packet(self) -> dict | None:
        """
        Đọc đúng 1 gói tin hoàn chỉnh từ socket.
        Trả về dict hoặc None nếu kết nối đứt.
        """
        # Đọc header 4 bytes để biết độ dài gói tin
        header = self._recv_exactly(4)
        if header is None:
            return None

        # Giải mã độ dài
        msg_len = struct.unpack(">I", header)[0]

        # Đọc đúng msg_len bytes dữ liệu
        data = self._recv_exactly(msg_len)
        if data is None:
            return None

        return decode_packet(data)

    def _recv_exactly(self, n: int) -> bytes | None:
        """Đọc đúng n bytes từ socket."""
        data = b""
        while len(data) < n:
            try:
                chunk = self.sock.recv(n - len(data))
                if not chunk:
                    return None  # Kết nối đã đóng
                data += chunk
            except Exception:
                return None
        return data


# -------------------------
# HẰNG SỐ GAME
# -------------------------

class GameConfig:
    # Kích thước bản đồ thế giới
    WORLD_WIDTH     = 4000
    WORLD_HEIGHT    = 4000

    # Tốc độ game server
    SERVER_TICKRATE = 30        # frames/giây server cập nhật
    INPUT_RATE      = 60        # frames/giây client gửi input

    # Cấu hình rắn
    SNAKE_SPEED         = 3.0   # pixel/frame mặc định
    SNAKE_BOOST_SPEED   = 6.0   # pixel/frame khi boost
    SNAKE_RADIUS        = 10    # bán kính đầu rắn
    SNAKE_SEGMENT_DIST  = 8     # khoảng cách giữa các đốt thân
    INITIAL_LENGTH      = 30    # số đốt ban đầu
    BOOST_LENGTH_COST   = 1     # giảm 1 đốt / X frame khi boost
    BOOST_COST_INTERVAL = 10    # interval giảm đốt khi boost (frames)

    # Cấu hình mồi
    FOOD_RADIUS         = 6     # bán kính hạt mồi thường
    FOOD_SCORE          = 1     # điểm khi ăn mồi thường
    DEATH_FOOD_RADIUS   = 9     # bán kính mồi từ xác
    DEATH_FOOD_SCORE    = 5     # điểm khi ăn mồi xác
    FOOD_COUNT_BASE     = 300   # số hạt mồi tối thiểu trên map
    FOOD_SPAWN_RATE     = 10    # sinh thêm bao nhiêu mồi/tick khi thiếu

    # Cấu hình phòng
    MAX_ROOM_PLAYERS    = 10
    MIN_START_PLAYERS   = 1     # cho phép chơi 1 mình để test

    # Mạng
    SERVER_HOST         = "127.0.0.1"
    SERVER_PORT         = 12345
    SOCKET_TIMEOUT      = 30    # giây timeout

    # Màu sắc mặc định cho rắn (HEX)
    DEFAULT_SNAKE_COLORS = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4",
        "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F",
        "#BB8FCE", "#85C1E9", "#82E0AA", "#F1948A",
    ]
