# =============================================================================
# client/network.py - Quản lý kết nối mạng phía Client
# Môn: Lập Trình Mạng | Game Rắn Săn Mồi Multiplayer
# =============================================================================

import socket
import threading
import queue
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.protocol import PacketType, encode_packet, PacketReader, GameConfig

logger = logging.getLogger("CLIENT.NET")


class NetworkClient:
    """
    Quản lý kết nối Socket TCP tới game server.
    Chạy luồng nhận dữ liệu riêng biệt để không block game loop.
    Tất cả gói tin nhận được đặt vào queue để game loop xử lý.
    """

    def __init__(self):
        self.sock: socket.socket | None = None
        self.reader: PacketReader | None = None
        self.connected = False
        self.running = False

        # Queue nhận gói tin (thread-safe)
        self.recv_queue: queue.Queue = queue.Queue(maxsize=500)

        # Thread nhận dữ liệu
        self._recv_thread: threading.Thread | None = None

    def connect(self, host: str = GameConfig.SERVER_HOST,
                port: int = GameConfig.SERVER_PORT,
                timeout: float = 10.0) -> bool:
        """
        Kết nối tới server.
        Trả về True nếu thành công, False nếu thất bại.
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            self.sock.connect((host, port))
            self.sock.settimeout(GameConfig.SOCKET_TIMEOUT)
            self.reader = PacketReader(self.sock)
            self.connected = True
            self.running = True

            # Khởi chạy luồng nhận
            self._recv_thread = threading.Thread(
                target=self._recv_loop,
                daemon=True
            )
            self._recv_thread.start()
            logger.info(f"✅ Kết nối tới {host}:{port}")
            return True

        except (ConnectionRefusedError, TimeoutError, OSError) as e:
            logger.error(f"❌ Không thể kết nối: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Ngắt kết nối."""
        self.running = False
        self.connected = False
        if self.sock:
            try:
                self.send(PacketType.DISCONNECT, {})
                self.sock.close()
            except Exception:
                pass
        logger.info("Ngắt kết nối khỏi server")

    # -------------------------
    # LUỒNG NHẬN DỮ LIỆU
    # -------------------------

    def _recv_loop(self):
        """Luồng đọc gói tin liên tục từ server."""
        while self.running and self.connected:
            try:
                packet = self.reader.read_packet()
                if packet is None:
                    logger.warning("Kết nối bị ngắt từ server")
                    break
                # Đặt vào queue (non-blocking, bỏ qua nếu queue đầy)
                try:
                    self.recv_queue.put_nowait(packet)
                except queue.Full:
                    # Queue đầy - bỏ gói tin cũ nhất
                    try:
                        self.recv_queue.get_nowait()
                    except queue.Empty:
                        pass
                    self.recv_queue.put_nowait(packet)
            except Exception as e:
                logger.debug(f"Lỗi recv loop: {e}")
                break

        self.connected = False
        # Gửi sự kiện ngắt kết nối vào queue
        try:
            self.recv_queue.put_nowait({
                "type": "CONNECTION_LOST",
                "payload": {"message": "Mất kết nối với server!"}
            })
        except Exception:
            pass

    def get_packets(self) -> list:
        """Lấy tất cả gói tin đang chờ xử lý trong queue."""
        packets = []
        while True:
            try:
                packets.append(self.recv_queue.get_nowait())
            except queue.Empty:
                break
        return packets

    # -------------------------
    # GỬI GÓI TIN
    # -------------------------

    def send(self, packet_type: str, payload: dict) -> bool:
        """Gửi gói tin tới server."""
        if not self.connected or not self.sock:
            return False
        try:
            data = encode_packet(packet_type, payload)
            self.sock.sendall(data)
            return True
        except Exception as e:
            logger.debug(f"Lỗi gửi gói tin: {e}")
            self.connected = False
            return False

    # -------------------------
    # CÁC HÀM TIỆN ÍCH GỬI GÓI TIN
    # -------------------------

    def login(self, username: str, password: str):
        return self.send(PacketType.LOGIN_REQ, {"username": username, "password": password})

    def register(self, username: str, password: str, display_name: str = None):
        return self.send(PacketType.REGISTER_REQ, {
            "username": username,
            "password": password,
            "display_name": display_name or username
        })

    def request_room_list(self):
        return self.send(PacketType.ROOM_LIST_REQ, {})

    def create_room(self, room_name: str, max_players: int = 10):
        return self.send(PacketType.CREATE_ROOM_REQ, {
            "room_name": room_name,
            "max_players": max_players
        })

    def join_room(self, room_id: str):
        return self.send(PacketType.JOIN_ROOM_REQ, {"room_id": room_id})

    def leave_room(self):
        return self.send(PacketType.LEAVE_ROOM_REQ, {})

    def start_game(self):
        return self.send(PacketType.START_GAME_REQ, {})

    def send_input(self, angle: float, is_boosting: bool):
        return self.send(PacketType.PLAYER_INPUT, {
            "angle": round(angle, 4),
            "is_boosting": is_boosting
        })

    def send_chat(self, message: str):
        return self.send(PacketType.CHAT_MSG, {"message": message})

    def request_respawn(self):
        return self.send(PacketType.RESPAWN_REQ, {})

    def update_skin(self, skin_color: str):
        return self.send(PacketType.UPDATE_SKIN_REQ, {"skin_color": skin_color})

    def request_leaderboard(self):
        return self.send(PacketType.LEADERBOARD_REQ, {})
