# =============================================================================
# client/client.py - Game Client chính (Pygame App)
# Quản lý game loop, xử lý sự kiện, kết nối mạng và render
# Môn: Lập Trình Mạng | Game Rắn Săn Mồi Multiplayer
# =============================================================================

import pygame
import math
import sys
import os
import time
import threading

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.protocol import PacketType, GameConfig
from client.network import NetworkClient
from client.renderer import Renderer
from client.ui_screens import (
    MainMenuScreen, AuthScreen, LobbyScreen,
    RoomWaitingScreen, LeaderboardScreen
)


class SlitherClient:
    """
    Game Client chính - Quản lý toàn bộ vòng lặp game, màn hình
    và giao tiếp mạng.
    """

    # Các trạng thái màn hình
    STATE_MAIN_MENU  = "main_menu"
    STATE_LOGIN      = "login"
    STATE_REGISTER   = "register"
    STATE_LOBBY      = "lobby"
    STATE_ROOM_WAIT  = "room_wait"
    STATE_PLAYING    = "playing"
    STATE_GAME_OVER  = "game_over"
    STATE_LEADERBOARD = "leaderboard"
    STATE_CONNECTING = "connecting"

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("🐍 Slither.io - Multiplayer Snake Battle")

        # Thiết lập màn hình
        self.WIDTH  = 1280
        self.HEIGHT = 720
        self.screen = pygame.display.set_mode(
            (self.WIDTH, self.HEIGHT),
            pygame.RESIZABLE
        )

        # Try set icon (bỏ qua nếu không có file)
        try:
            icon = pygame.Surface((32, 32))
            icon.fill((0, 0, 0))
            pygame.draw.circle(icon, (80, 220, 100), (16, 16), 14)
            pygame.display.set_icon(icon)
        except Exception:
            pass

        self.clock   = pygame.time.Clock()
        self.running = True
        self.FPS     = 60

        # Modules
        self.network  = NetworkClient()
        self.renderer = Renderer(self.screen)

        # Fonts (dùng chung, ưu tiên font hỗ trợ Unicode tiếng Việt đầy đủ)
        pygame.font.init()
        font_candidates = ["Segoe UI", "Arial", "Tahoma", "Calibri", "Helvetica", None]
        self.fonts = {}
        for fn in font_candidates:
            try:
                self.fonts = {
                    "small":   pygame.font.SysFont(fn, 14),
                    "medium":  pygame.font.SysFont(fn, 18),
                    "large":   pygame.font.SysFont(fn, 24),
                    "xlarge":  pygame.font.SysFont(fn, 36),
                    "title":   pygame.font.SysFont(fn, 52, bold=True),
                }
                # Kiểm tra render ký tự tiếng Việt có dấu
                test_str = "Tiếng Việt có dấu: Ắ, Ằ, Ộ, Ớ, Ừ"
                self.fonts["small"].render(test_str, True, (255, 255, 255))
                break
            except Exception:
                continue

        # Trạng thái ứng dụng
        self.state = self.STATE_MAIN_MENU
        self.prev_state = None

        # Dữ liệu người chơi
        self.player_id: str | None  = None
        self.player_info: dict = {}

        # Dữ liệu phòng
        self.current_room_id: str | None = None
        self.room_info: dict = {}
        self.player_list: list = []

        # Dữ liệu game
        self.world_state: dict = {}
        self.my_snake_data: dict = {}
        self.chat_messages: list = []
        self.game_leaderboard: list = []
        self.last_score = 0
        self.last_length = 0
        self.last_kills = 0
        self.last_time_alive = 0
        self.game_start_time = 0
        self.dead = False
        self.food_eaten_positions: list = []  # Para partículas

        # Camera (World Space -> Screen Space)
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.cam_target_x = 0.0
        self.cam_target_y = 0.0
        self.cam_lerp = 0.12

        # Màn hình hiện tại
        self.current_screen = None

        # Server config
        self.server_host = GameConfig.SERVER_HOST
        self.server_port = GameConfig.SERVER_PORT

        # Input gửi lên server
        self.input_timer = 0
        self.input_interval = max(1, int(self.FPS / GameConfig.INPUT_RATE))

        # Leaderboard data
        self.leaderboard_data: list = []

        # Initialize main menu
        self._goto_main_menu()

        # Thông báo lỗi tạm thời
        self.temp_message = ""
        self.temp_msg_timer = 0

    # =========================================================================
    # VÒNG LẶP CHÍNH
    # =========================================================================

    def run(self):
        """Vòng lặp game chính."""
        while self.running:
            dt = self.clock.tick(self.FPS) / 1000.0

            # Xử lý events Pygame
            self._handle_events()

            # Xử lý gói tin mạng đến
            self._process_network_packets()

            # Cập nhật trạng thái
            self._update(dt)

            # Render
            self._render(dt)

            pygame.display.flip()

        # Dọn dẹp
        if self.network.connected:
            self.network.disconnect()
        pygame.quit()
        sys.exit(0)

    # =========================================================================
    # XỬ LÝ EVENTS PYGAME
    # =========================================================================

    def _handle_events(self):
        """Xử lý tất cả sự kiện Pygame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.VIDEORESIZE:
                self.WIDTH = event.w
                self.HEIGHT = event.h
                self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
                self.renderer = Renderer(self.screen)
                self._rebuild_screen()
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._handle_escape()

            # Chuyển event cho màn hình hiện tại
            self._dispatch_event(event)

    def _handle_escape(self):
        """Xử lý phím ESC."""
        if self.state == self.STATE_PLAYING:
            # Xác nhận thoát phòng
            self._leave_room()
        elif self.state in (self.STATE_LOGIN, self.STATE_REGISTER):
            self._goto_main_menu()
        elif self.state == self.STATE_ROOM_WAIT:
            self._leave_room()
        elif self.state == self.STATE_LEADERBOARD:
            self._goto_lobby()
        elif self.state == self.STATE_GAME_OVER:
            self._leave_room()

    def _dispatch_event(self, event: pygame.event.Event):
        """Phân phối event tới màn hình đang hiển thị."""
        if self.state == self.STATE_MAIN_MENU:
            if event.type == pygame.MOUSEBUTTONDOWN:
                action = self.current_screen.handle_click(event.pos)
                self._handle_main_menu_action(action)

        elif self.state in (self.STATE_LOGIN, self.STATE_REGISTER):
            result = self.current_screen.handle_event(event)
            if result:
                self._handle_auth_action(result)

        elif self.state == self.STATE_LOBBY:
            result = self.current_screen.handle_event(event)
            if result:
                self._handle_lobby_action(result)

        elif self.state == self.STATE_ROOM_WAIT:
            result = self.current_screen.handle_event(event)
            if result:
                self._handle_room_wait_action(result)

        elif self.state == self.STATE_PLAYING:
            self._handle_playing_events(event)

        elif self.state == self.STATE_GAME_OVER:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self._handle_respawn()
                elif event.key == pygame.K_ESCAPE:
                    self._leave_room()

        elif self.state == self.STATE_LEADERBOARD:
            if event.type == pygame.MOUSEBUTTONDOWN:
                action = self.current_screen.handle_click(event.pos)
                if action == "back":
                    self._goto_lobby()

    def _handle_playing_events(self, event: pygame.event.Event):
        """Xử lý sự kiện khi đang chơi."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Toggle chat mode
                self._toggle_chat_input()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                pass  # Click trái để boost (xử lý ở update)

    # =========================================================================
    # XỬ LÝ ACTIONS TỪ CÁC MÀN HÌNH
    # =========================================================================

    def _handle_main_menu_action(self, action: str | None):
        if action == "login":
            self._goto_auth("login")
        elif action == "register":
            self._goto_auth("register")
        elif action == "leaderboard":
            self.network.request_leaderboard()
            self._goto_leaderboard([])
        elif action == "quit":
            self.running = False

    def _handle_auth_action(self, result: dict):
        action = result.get("action")
        data = result.get("data", {})

        if action == "back":
            self._goto_main_menu()
            return

        if not self.network.connected:
            self.current_screen.set_message("⏳ Đang kết nối tới server...")
            self.current_screen.loading = True

            def try_connect():
                ok = self.network.connect(self.server_host, self.server_port)
                if not ok:
                    self.current_screen.set_message(
                        f"❌ Không thể kết nối tới server {self.server_host}:{self.server_port}!")
                else:
                    if action == "login":
                        self.network.login(data.get("username", ""), data.get("password", ""))
                    elif action == "register":
                        self.network.register(data.get("username", ""),
                                              data.get("password", ""),
                                              data.get("display_name", ""))

            threading.Thread(target=try_connect, daemon=True).start()
        else:
            self.current_screen.loading = True
            if action == "login":
                self.network.login(data.get("username", ""), data.get("password", ""))
            elif action == "register":
                self.network.register(data.get("username", ""),
                                      data.get("password", ""),
                                      data.get("display_name", ""))

    def _handle_lobby_action(self, result: dict):
        action = result.get("action")
        if action == "logout":
            self.network.disconnect()
            self.player_info = {}
            self.player_id = None
            self._goto_main_menu()
        elif action == "refresh":
            self.network.request_room_list()
        elif action == "create_room":
            self.network.create_room(result.get("room_name", "Phòng vui"))
        elif action == "join_room":
            self.network.join_room(result.get("room_id"))
        elif action == "leaderboard":
            self.network.request_leaderboard()
        elif action == "update_skin":
            self.network.update_skin(result.get("skin_color", "#4ECDC4"))
            self.player_info["skin_color"] = result.get("skin_color", "#4ECDC4")
            self.current_screen.show_message("✅ Đã lưu skin!")

    def _handle_room_wait_action(self, result: dict):
        action = result.get("action")
        if action == "leave":
            self._leave_room()
        elif action == "start":
            self.network.start_game()
        elif action == "chat":
            self.network.send_chat(result.get("message", ""))

    def _handle_respawn(self):
        """Yêu cầu hồi sinh."""
        self.network.request_respawn()
        self.dead = False
        self.game_start_time = time.time()
        self.state = self.STATE_PLAYING

    # =========================================================================
    # XỬ LÝ GÓI TIN MẠNG
    # =========================================================================

    def _process_network_packets(self):
        """Xử lý tất cả gói tin đến từ server."""
        packets = self.network.get_packets()
        for packet in packets:
            self._handle_packet(packet)

    def _handle_packet(self, packet: dict):
        ptype = packet.get("type")
        payload = packet.get("payload", {})

        if ptype == PacketType.LOGIN_RES:
            self._on_login_res(payload)
        elif ptype == PacketType.REGISTER_RES:
            self._on_register_res(payload)
        elif ptype == PacketType.ROOM_LIST_RES:
            self._on_room_list(payload)
        elif ptype in (PacketType.CREATE_ROOM_RES, PacketType.JOIN_ROOM_RES):
            self._on_join_room(payload)
        elif ptype == PacketType.ROOM_UPDATE:
            self._on_room_update(payload)
        elif ptype == PacketType.GAME_START:
            self._on_game_start(payload)
        elif ptype == PacketType.WORLD_STATE:
            self._on_world_state(payload)
        elif ptype == PacketType.PLAYER_DEAD:
            self._on_player_dead(payload)
        elif ptype == PacketType.CHAT_BROADCAST:
            self._on_chat(payload)
        elif ptype == PacketType.LEADERBOARD_RES:
            self._on_leaderboard(payload)
        elif ptype == PacketType.UPDATE_SKIN_RES:
            pass  # Đã xử lý ở lobby
        elif ptype == PacketType.ERROR_MSG:
            self._show_temp_message(payload.get("message", "Lỗi!"))
        elif ptype == "CONNECTION_LOST":
            self._on_connection_lost(payload)

    def _on_login_res(self, payload: dict):
        if payload.get("success"):
            self.player_id = payload.get("player_id")
            self.player_info = payload.get("user", {})
            self._goto_lobby()
        else:
            if hasattr(self.current_screen, 'set_message'):
                self.current_screen.set_message(payload.get("message", "Đăng nhập thất bại!"))

    def _on_register_res(self, payload: dict):
        if payload.get("success"):
            if hasattr(self.current_screen, 'set_message'):
                self.current_screen.set_message("✅ Đăng ký thành công! Hãy đăng nhập.", success=True)
        else:
            if hasattr(self.current_screen, 'set_message'):
                self.current_screen.set_message(payload.get("message", "Đăng ký thất bại!"))

    def _on_room_list(self, payload: dict):
        if self.state == self.STATE_LOBBY and hasattr(self.current_screen, 'rooms'):
            self.current_screen.rooms = payload.get("rooms", [])

    def _on_join_room(self, payload: dict):
        if not payload.get("success"):
            self._show_temp_message(payload.get("message", "Không thể vào phòng!"))
            return
        self.current_room_id = payload.get("room_id")
        self.room_info = payload.get("room_info", {})
        self.player_list = payload.get("player_list", [])
        self._goto_room_wait()

    def _on_room_update(self, payload: dict):
        self.room_info = payload.get("room_info", self.room_info)
        self.player_list = payload.get("player_list", self.player_list)
        if self.state == self.STATE_ROOM_WAIT:
            self.current_screen.room_info = self.room_info
            self.current_screen.player_list = self.player_list
            # Kiểm tra có phải host không
            username = self.player_info.get("username", "")
            self.current_screen.is_host = self.room_info.get("host") == username

    def _on_game_start(self, payload: dict):
        self._goto_playing()

    def _on_world_state(self, payload: dict):
        if self.state not in (self.STATE_PLAYING, self.STATE_GAME_OVER):
            return

        self.world_state = payload
        # Cập nhật dữ liệu rắn của bản thân
        snakes = payload.get("snakes", {})
        if self.player_id and self.player_id in snakes:
            self.my_snake_data = snakes[self.player_id]
            # Cập nhật camera target
            self.cam_target_x = self.my_snake_data["x"] - self.WIDTH / 2
            self.cam_target_y = self.my_snake_data["y"] - self.HEIGHT / 2

        self.game_leaderboard = payload.get("leaderboard", [])

    def _on_player_dead(self, payload: dict):
        if payload.get("player_id") == self.player_id:
            self.dead = True
            self.last_score = payload.get("score", 0)
            self.last_length = payload.get("max_length", 0)
            self.last_kills = payload.get("kills", 0)
            self.last_time_alive = payload.get("time_alive", 0)
            self.state = self.STATE_GAME_OVER

    def _on_chat(self, payload: dict):
        self.chat_messages.append(payload)
        if len(self.chat_messages) > 50:
            self.chat_messages = self.chat_messages[-50:]
        # Cập nhật màn hình phòng chờ nếu đang ở đó
        if self.state == self.STATE_ROOM_WAIT:
            self.current_screen.chat_messages = self.chat_messages

    def _on_leaderboard(self, payload: dict):
        self.leaderboard_data = payload.get("leaderboard", [])
        self._goto_leaderboard(self.leaderboard_data)

    def _on_connection_lost(self, payload: dict):
        self._show_temp_message("❌ Mất kết nối với server!")
        self.player_id = None
        self._goto_main_menu()

    # =========================================================================
    # CẬP NHẬT TRẠNG THÁI
    # =========================================================================

    def _update(self, dt: float):
        """Cập nhật logic theo frame."""
        # Cập nhật màn hình hiện tại
        if self.current_screen and hasattr(self.current_screen, 'update'):
            self.current_screen.update(dt)

        # Cập nhật renderer animation
        self.renderer.update(dt)

        # Camera lerp (mượt mà)
        self.cam_x += (self.cam_target_x - self.cam_x) * self.cam_lerp
        self.cam_y += (self.cam_target_y - self.cam_y) * self.cam_lerp

        # Clamp camera
        self.cam_x = max(0, min(GameConfig.WORLD_WIDTH - self.WIDTH, self.cam_x))
        self.cam_y = max(0, min(GameConfig.WORLD_HEIGHT - self.HEIGHT, self.cam_y))

        # Gửi input khi đang chơi
        if self.state == self.STATE_PLAYING and not self.dead:
            self.input_timer += 1
            if self.input_timer >= self.input_interval:
                self.input_timer = 0
                self._send_player_input()

        # Timer thông báo tạm
        if self.temp_msg_timer > 0:
            self.temp_msg_timer -= 1

    def _send_player_input(self):
        """Gửi input chuột lên server."""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # Tính tọa độ world của chuột
        world_mouse_x = mouse_x + self.cam_x
        world_mouse_y = mouse_y + self.cam_y

        # Tính góc từ đầu rắn tới chuột
        if self.my_snake_data:
            dx = world_mouse_x - self.my_snake_data.get("x", 0)
            dy = world_mouse_y - self.my_snake_data.get("y", 0)
            angle = math.atan2(dy, dx)
        else:
            angle = 0.0

        # Boost khi giữ chuột trái hoặc Space
        keys = pygame.key.get_pressed()
        mouse_btns = pygame.mouse.get_pressed()
        is_boosting = mouse_btns[0] or keys[pygame.K_SPACE]

        self.network.send_input(angle, is_boosting)

    # =========================================================================
    # RENDER
    # =========================================================================

    def _render(self, dt: float):
        """Vẽ frame hiện tại."""
        if self.state == self.STATE_MAIN_MENU:
            self.current_screen.draw()

        elif self.state in (self.STATE_LOGIN, self.STATE_REGISTER):
            self.current_screen.draw()

        elif self.state == self.STATE_LOBBY:
            self.current_screen.draw()

        elif self.state == self.STATE_ROOM_WAIT:
            self.current_screen.draw()

        elif self.state in (self.STATE_PLAYING, self.STATE_GAME_OVER):
            self._render_game()
            if self.state == self.STATE_GAME_OVER:
                # Tính thứ hạng
                rank = 1
                total = len(self.world_state.get("snakes", {})) + 1
                lb = self.game_leaderboard
                for i, entry in enumerate(lb):
                    if entry.get("player_id") == self.player_id:
                        rank = i + 1
                        break
                self.renderer.draw_game_over(
                    self.last_score, self.last_length, self.last_kills,
                    self.last_time_alive, rank, total
                )

        elif self.state == self.STATE_LEADERBOARD:
            self.current_screen.draw()

        elif self.state == self.STATE_CONNECTING:
            self.renderer.draw_loading("Đang kết nối tới server...")

        # Thông báo tạm
        if self.temp_msg_timer > 0 and self.temp_message:
            self._draw_temp_message()

    def _render_game(self):
        """Render màn hình game chính."""
        cam_x, cam_y = self.cam_x, self.cam_y

        # Nền
        self.renderer.draw_background(cam_x, cam_y)

        # Viền bản đồ
        self.renderer.draw_world_border(cam_x, cam_y)

        # Lấy dữ liệu world state
        snakes = self.world_state.get("snakes", {})
        foods = self.world_state.get("foods", [])

        # Vẽ thức ăn
        self.renderer.draw_foods(foods, cam_x, cam_y)

        # Vẽ rắn (bản thân vẽ sau cùng để ở trên cùng)
        my_id = self.player_id
        for pid, snake_data in snakes.items():
            if pid != my_id:
                self.renderer.draw_snake(snake_data, cam_x, cam_y, is_self=False)

        # Vẽ rắn của bản thân
        if my_id and my_id in snakes:
            self.renderer.draw_snake(snakes[my_id], cam_x, cam_y, is_self=True)

        # Vẽ particles
        self.renderer.draw_particles()

        # HUD
        my_score = self.my_snake_data.get("score", 0) if self.my_snake_data else 0
        my_length = self.my_snake_data.get("length", 0) if self.my_snake_data else 0
        self.renderer.draw_hud(my_score, my_length, self.game_leaderboard, self.player_id or "")

        # Minimap
        self.renderer.draw_minimap(snakes, my_id or "", cam_x, cam_y)

        # Chat
        self.renderer.draw_chat(self.chat_messages)

        # Hướng dẫn điều khiển (hiển thị 10 giây đầu)
        elapsed = time.time() - self.game_start_time
        if elapsed < 10:
            hint = self.fonts["medium"].render(
                "🖱️  Di chuột để điều hướng  |  Giữ chuột trái / SPACE để bứt tốc",
                True, (180, 180, 220))
            alpha = min(255, int(255 * (10 - elapsed) / 3))
            hint.set_alpha(alpha)
            self.screen.blit(hint, (self.WIDTH//2 - hint.get_width()//2, self.HEIGHT - 40))

    def _draw_temp_message(self):
        """Vẽ thông báo tạm thời giữa màn hình."""
        alpha = min(255, self.temp_msg_timer * 8)
        surf = self.fonts["large"].render(self.temp_message, True, (255, 200, 100))
        surf.set_alpha(alpha)
        x = self.WIDTH // 2 - surf.get_width() // 2
        y = self.HEIGHT // 2 - 80
        # Background
        bg = pygame.Surface((surf.get_width() + 30, surf.get_height() + 16), pygame.SRCALPHA)
        bg.fill((0, 0, 0, int(alpha * 0.7)))
        self.screen.blit(bg, (x - 15, y - 8))
        self.screen.blit(surf, (x, y))

    # =========================================================================
    # ĐIỀU HƯỚNG MÀN HÌNH
    # =========================================================================

    def _goto_main_menu(self):
        self.state = self.STATE_MAIN_MENU
        self.current_screen = MainMenuScreen(self.screen, self.fonts)

    def _goto_auth(self, mode: str):
        self.state = self.STATE_LOGIN if mode == "login" else self.STATE_REGISTER
        self.current_screen = AuthScreen(self.screen, self.fonts, mode)

    def _goto_lobby(self):
        self.state = self.STATE_LOBBY
        self.current_screen = LobbyScreen(self.screen, self.fonts, self.player_info)
        # Tự động refresh danh sách phòng
        if self.network.connected:
            self.network.request_room_list()

    def _goto_room_wait(self):
        self.state = self.STATE_ROOM_WAIT
        self.current_screen = RoomWaitingScreen(
            self.screen, self.fonts, self.room_info, self.player_info)
        self.current_screen.player_list = self.player_list
        self.current_screen.chat_messages = self.chat_messages
        # Check host
        username = self.player_info.get("username", "")
        self.current_screen.is_host = self.room_info.get("host") == username

    def _goto_playing(self):
        self.state = self.STATE_PLAYING
        self.current_screen = None
        self.dead = False
        self.world_state = {}
        self.my_snake_data = {}
        self.chat_messages = []
        self.game_start_time = time.time()
        # Khởi tạo camera ở giữa bản đồ
        self.cam_x = GameConfig.WORLD_WIDTH / 2 - self.WIDTH / 2
        self.cam_y = GameConfig.WORLD_HEIGHT / 2 - self.HEIGHT / 2
        self.cam_target_x = self.cam_x
        self.cam_target_y = self.cam_y

    def _goto_leaderboard(self, data: list):
        self.state = self.STATE_LEADERBOARD
        self.leaderboard_data = data
        self.current_screen = LeaderboardScreen(self.screen, self.fonts, data)

    def _leave_room(self):
        """Rời phòng và về lobby."""
        if self.network.connected:
            self.network.leave_room()
        self.current_room_id = None
        self.room_info = {}
        self.player_list = []
        self.chat_messages = []
        self.world_state = {}
        self.dead = False
        if self.player_info:
            self._goto_lobby()
        else:
            self._goto_main_menu()

    def _rebuild_screen(self):
        """Rebuild màn hình sau khi resize."""
        if self.state == self.STATE_MAIN_MENU:
            self._goto_main_menu()
        elif self.state == self.STATE_LOBBY:
            self._goto_lobby()

    def _toggle_chat_input(self):
        """Toggle chat input khi đang chơi."""
        pass  # Chat xử lý ở renderer

    def _show_temp_message(self, msg: str, duration_frames: int = 120):
        """Hiển thị thông báo tạm thời."""
        self.temp_message = msg
        self.temp_msg_timer = duration_frames


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """Hàm khởi chạy game client."""
    import argparse
    parser = argparse.ArgumentParser(description="Slither.io Game Client")
    parser.add_argument("--host", default=GameConfig.SERVER_HOST, help="Server IP")
    parser.add_argument("--port", type=int, default=GameConfig.SERVER_PORT, help="Server Port")
    args = parser.parse_args()

    client = SlitherClient()
    client.server_host = args.host
    client.server_port = args.port
    client.run()


if __name__ == "__main__":
    main()
