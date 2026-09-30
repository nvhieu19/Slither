# =============================================================================
# client/renderer.py - Module Đồ Họa (Pygame Renderer)
# Vẽ tất cả các thành phần giao diện game với hiệu ứng đẹp
# Môn: Lập Trình Mạng | Game Rắn Săn Mồi Multiplayer
# =============================================================================

import pygame
import math
import random
import time
from shared.protocol import GameConfig


# -------------------------
# HÀM TIỆN ÍCH MÀU SẮC
# -------------------------

def hex_to_rgb(hex_color: str) -> tuple:
    """Chuyển màu HEX (#RRGGBB) sang tuple RGB."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def darken(color: tuple, factor: float = 0.5) -> tuple:
    """Làm tối màu."""
    return tuple(max(0, int(c * factor)) for c in color[:3])


def lighten(color: tuple, factor: float = 1.5) -> tuple:
    """Làm sáng màu."""
    return tuple(min(255, int(c * factor)) for c in color[:3])


def lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    """Nội suy màu."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# -------------------------
# LỚP VẼ CHÍNH
# -------------------------

class Renderer:
    """
    Xử lý toàn bộ việc vẽ game lên màn hình Pygame.
    Sử dụng kỹ thuật Camera (World to Screen transform).
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()

        # Surface phụ để vẽ hiệu ứng phát sáng (Glow)
        self.glow_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Bộ đệm particle (mảnh vỡ khi ăn mồi)
        self.particles: list = []

        # Đồng hồ animation
        self.anim_time = 0.0

        # Load fonts
        pygame.font.init()
        self._load_fonts()

        # Cache surface rắn (tối ưu hiệu suất)
        self._snake_cache = {}

    def _load_fonts(self):
        """Load font hệ thống."""
        font_names = ["Arial", "Segoe UI", "Helvetica", None]
        self.font_small  = None
        self.font_medium = None
        self.font_large  = None
        self.font_xlarge = None
        self.font_title  = None

        for name in font_names:
            try:
                self.font_small  = pygame.font.SysFont(name, 14)
                self.font_medium = pygame.font.SysFont(name, 18)
                self.font_large  = pygame.font.SysFont(name, 24)
                self.font_xlarge = pygame.font.SysFont(name, 36)
                self.font_title  = pygame.font.SysFont(name, 64, bold=True)
                break
            except Exception:
                continue

    def update(self, dt: float):
        """Cập nhật trạng thái animation."""
        self.anim_time += dt
        # Cập nhật particles
        self.particles = [
            p for p in self.particles
            if p["life"] > 0
        ]
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.1  # trọng lực nhẹ
            p["life"] -= 1
            p["alpha"] = int(255 * p["life"] / p["max_life"])

    def spawn_eat_particles(self, screen_x: float, screen_y: float, color: tuple, count: int = 8):
        """Sinh hiệu ứng mảnh vỡ khi ăn mồi."""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 4)
            life = random.randint(15, 35)
            self.particles.append({
                "x": screen_x, "y": screen_y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "color": color,
                "radius": random.uniform(2, 5),
                "life": life, "max_life": life, "alpha": 255
            })

    # -------------------------
    # VẼ NỀN (BACKGROUND GRID)
    # -------------------------

    def draw_background(self, cam_x: float, cam_y: float):
        """Vẽ nền tối với lưới dọt."""
        # Nền gradient tối
        self.screen.fill((8, 10, 25))

        # Vẽ lưới
        grid_size = 80
        grid_color = (20, 25, 55)
        offset_x = int(cam_x % grid_size)
        offset_y = int(cam_y % grid_size)

        for x in range(-offset_x, self.width + grid_size, grid_size):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, self.height), 1)
        for y in range(-offset_y, self.height + grid_size, grid_size):
            pygame.draw.line(self.screen, grid_color, (0, y), (self.width, y), 1)

    def draw_world_border(self, cam_x: float, cam_y: float):
        """Vẽ viền bản đồ thế giới."""
        # Tọa độ góc của bản đồ trên màn hình
        world_left   = int(-cam_x)
        world_top    = int(-cam_y)
        world_right  = int(GameConfig.WORLD_WIDTH - cam_x)
        world_bottom = int(GameConfig.WORLD_HEIGHT - cam_y)

        border_color = (255, 80, 80)
        border_width = 4

        # Chỉ vẽ phần biên nằm trong màn hình
        rects = [
            pygame.Rect(world_left, world_top, GameConfig.WORLD_WIDTH, border_width),     # top
            pygame.Rect(world_left, world_bottom - border_width, GameConfig.WORLD_WIDTH, border_width),  # bottom
            pygame.Rect(world_left, world_top, border_width, GameConfig.WORLD_HEIGHT),    # left
            pygame.Rect(world_right - border_width, world_top, border_width, GameConfig.WORLD_HEIGHT),   # right
        ]
        for rect in rects:
            clipped = rect.clip(pygame.Rect(0, 0, self.width, self.height))
            if clipped.width > 0 and clipped.height > 0:
                # Hiệu ứng nhấp nháy viền đỏ
                alpha = int(180 + 75 * math.sin(self.anim_time * 4))
                glow_surf = pygame.Surface((clipped.width, clipped.height), pygame.SRCALPHA)
                glow_surf.fill((*border_color, alpha))
                self.screen.blit(glow_surf, (clipped.x, clipped.y))

    # -------------------------
    # VẼ THỨC ĂN (FOOD)
    # -------------------------

    def draw_foods(self, foods: list, cam_x: float, cam_y: float):
        """Vẽ tất cả hạt thức ăn với hiệu ứng phát sáng."""
        for food in foods:
            sx = food["x"] - cam_x
            sy = food["y"] - cam_y
            r = food["radius"]

            # Bỏ qua nếu ngoài màn hình
            if not (-r - 20 <= sx <= self.width + r + 20 and
                    -r - 20 <= sy <= self.height + r + 20):
                continue

            color = hex_to_rgb(food.get("color", "#4ECDC4"))
            pulse_phase = food.get("id", 0) * 0.5
            pulse = 0.7 + 0.3 * math.sin(self.anim_time * 3 + pulse_phase)

            if food.get("food_type") == "death":
                # Mồi xác: to hơn, sáng hơn
                draw_r = int(r * pulse * 1.2)
                glow_r = draw_r + 8
                # Vẽ glow
                glow_color = (*lighten(color, 1.3), 60)
                glow_surf = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, glow_color, (glow_r, glow_r), glow_r)
                self.screen.blit(glow_surf, (int(sx) - glow_r, int(sy) - glow_r))
            else:
                draw_r = max(3, int(r * pulse))
                glow_r = draw_r + 5
                glow_color = (*color, 50)
                glow_surf = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, glow_color, (glow_r, glow_r), glow_r)
                self.screen.blit(glow_surf, (int(sx) - glow_r, int(sy) - glow_r))

            # Vẽ hạt mồi chính
            pygame.draw.circle(self.screen, color, (int(sx), int(sy)), draw_r)
            # Điểm sáng nhỏ
            highlight = lighten(color, 2.0)
            pygame.draw.circle(self.screen, highlight,
                               (int(sx) - max(1, draw_r//3), int(sy) - max(1, draw_r//3)),
                               max(1, draw_r//4))

    # -------------------------
    # VẼ RẮN (SNAKE)
    # -------------------------

    def draw_snake(self, snake_data: dict, cam_x: float, cam_y: float,
                   is_self: bool = False):
        """Vẽ 1 con rắn với đầy đủ hiệu ứng."""
        segments = snake_data.get("segments", [])
        if len(segments) < 2:
            return

        color_hex = snake_data.get("skin_color", "#4ECDC4")
        color = hex_to_rgb(color_hex)
        dark_color = darken(color, 0.5)
        light_color = lighten(color, 1.4)

        is_boosting = snake_data.get("is_boosting", False)
        head_x = snake_data["x"] - cam_x
        head_y = snake_data["y"] - cam_y

        # Bỏ qua rắn quá xa màn hình
        if not (-200 <= head_x <= self.width + 200 and
                -200 <= head_y <= self.height + 200):
            return

        # --- VẼ THÂN RẮN ---
        n_segs = len(segments)
        for i in range(n_segs - 1, -1, -1):
            sx, sy = segments[i]
            sx -= cam_x
            sy -= cam_y

            if not (-30 <= sx <= self.width + 30 and -30 <= sy <= self.height + 30):
                continue

            # Kích thước đốt thân: giảm dần về đuôi
            t = i / max(n_segs - 1, 1)  # 0 = đầu, 1 = đuôi
            seg_r = max(3, int(GameConfig.SNAKE_RADIUS * (1.0 - t * 0.4)))

            # Màu gradient thân (đầu sáng, đuôi tối)
            seg_color = lerp_color(light_color, dark_color, t * 0.7)

            # Hiệu ứng boost: thân nhấp nháy
            if is_boosting and i % 4 < 2:
                seg_color = lighten(seg_color, 1.3)

            pygame.draw.circle(self.screen, seg_color, (int(sx), int(sy)), seg_r)

            # Đường viền đốt thân (mỗi 3 đốt)
            if i % 3 == 0 and seg_r > 4:
                pygame.draw.circle(self.screen, dark_color, (int(sx), int(sy)), seg_r, 1)

        # --- VẼ ĐẦU RẮN ---
        head_r = GameConfig.SNAKE_RADIUS + 3
        angle = snake_data.get("angle", 0)

        # Glow đầu rắn (to hơn nếu là bản thân)
        glow_r = head_r + (10 if is_self else 6)
        glow_alpha = 100 if is_self else 60
        glow_surf = pygame.Surface((glow_r*2+4, glow_r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*light_color, glow_alpha),
                           (glow_r+2, glow_r+2), glow_r)
        self.screen.blit(glow_surf, (int(head_x) - glow_r - 2, int(head_y) - glow_r - 2))

        # Đầu chính
        pygame.draw.circle(self.screen, color, (int(head_x), int(head_y)), head_r)
        # Viền đầu
        pygame.draw.circle(self.screen, light_color, (int(head_x), int(head_y)), head_r, 2)

        # --- VẼ MẮT RẮN ---
        eye_offset = head_r * 0.5
        # 2 mắt - tính vị trí theo góc di chuyển
        perp = angle + math.pi / 2
        for sign in (1, -1):
            ex = head_x + math.cos(angle) * eye_offset * 0.7 + math.cos(perp) * eye_offset * 0.5 * sign
            ey = head_y + math.sin(angle) * eye_offset * 0.7 + math.sin(perp) * eye_offset * 0.5 * sign
            # Lòng trắng
            pygame.draw.circle(self.screen, (240, 240, 240), (int(ex), int(ey)), 4)
            # Con ngươi
            pygame.draw.circle(self.screen, (20, 20, 20), (int(ex), int(ey)), 2)
            # Điểm sáng mắt
            pygame.draw.circle(self.screen, (255, 255, 255), (int(ex)+1, int(ey)-1), 1)

        # --- TÊN NGƯỜI CHƠI ---
        display_name = snake_data.get("display_name", snake_data.get("username", ""))
        if display_name:
            name_color = (255, 255, 100) if is_self else (220, 220, 220)
            name_surf = self.font_small.render(display_name, True, name_color)
            # Shadow
            shadow_surf = self.font_small.render(display_name, True, (0, 0, 0))
            nx = int(head_x) - name_surf.get_width() // 2
            ny = int(head_y) - head_r - 18
            self.screen.blit(shadow_surf, (nx + 1, ny + 1))
            self.screen.blit(name_surf, (nx, ny))

        # --- HIỆU ỨNG BOOST ---
        if is_boosting:
            # Vệt sáng phía sau đầu
            tail_x = head_x - math.cos(angle) * head_r * 2
            tail_y = head_y - math.sin(angle) * head_r * 2
            boost_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
            boost_alpha = int(150 * (0.5 + 0.5 * math.sin(self.anim_time * 20)))
            pygame.draw.circle(boost_surf, (*light_color, boost_alpha), (20, 20), 12)
            self.screen.blit(boost_surf, (int(tail_x) - 20, int(tail_y) - 20))

    # -------------------------
    # VẼ PARTICLES
    # -------------------------

    def draw_particles(self):
        """Vẽ tất cả particle hiệu ứng."""
        for p in self.particles:
            if p["alpha"] <= 0:
                continue
            r = max(1, int(p["radius"] * p["life"] / p["max_life"]))
            surf = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p["color"], p["alpha"]), (r+1, r+1), r)
            self.screen.blit(surf, (int(p["x"]) - r, int(p["y"]) - r))

    # -------------------------
    # VẼ HUD
    # -------------------------

    def draw_hud(self, my_score: int, my_length: int, leaderboard: list,
                 player_id: str):
        """Vẽ toàn bộ HUD in-game."""
        self._draw_score_bar(my_score, my_length)
        self._draw_leaderboard(leaderboard, player_id)

    def _draw_score_bar(self, score: int, length: int):
        """Thanh điểm phía trên."""
        bar_h = 42
        bar_surf = pygame.Surface((self.width, bar_h), pygame.SRCALPHA)
        bar_surf.fill((0, 0, 0, 140))
        self.screen.blit(bar_surf, (0, 0))

        # Score
        score_text = self.font_large.render(f"🏆 Điểm: {score}", True, (255, 220, 50))
        self.screen.blit(score_text, (20, 10))

        # Length
        len_text = self.font_large.render(f"🐍 Chiều dài: {length}", True, (100, 220, 100))
        self.screen.blit(len_text, (self.width // 2 - 80, 10))

    def _draw_leaderboard(self, leaderboard: list, player_id: str):
        """Bảng xếp hạng top 10 góc phải."""
        panel_w = 220
        panel_h = 30 + len(leaderboard) * 28 + 10
        panel_x = self.width - panel_w - 15
        panel_y = 55

        # Nền panel
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((0, 0, 0, 150))
        pygame.draw.rect(panel_surf, (100, 100, 255, 180), (0, 0, panel_w, panel_h), 2, border_radius=8)
        self.screen.blit(panel_surf, (panel_x, panel_y))

        # Tiêu đề
        title = self.font_medium.render("🏅 BXH PHÒNG", True, (200, 200, 255))
        self.screen.blit(title, (panel_x + 8, panel_y + 6))

        # Danh sách
        for i, entry in enumerate(leaderboard[:10]):
            y = panel_y + 34 + i * 28
            is_me = entry.get("player_id") == player_id

            # Màu nền cho bản thân
            if is_me:
                highlight = pygame.Surface((panel_w - 4, 26), pygame.SRCALPHA)
                highlight.fill((100, 200, 100, 80))
                self.screen.blit(highlight, (panel_x + 2, y - 2))

            # Số thứ hạng
            rank_colors = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]
            rank_color = rank_colors[i] if i < 3 else (180, 180, 180)
            rank_text = self.font_small.render(f"#{i+1}", True, rank_color)
            self.screen.blit(rank_text, (panel_x + 8, y))

            # Tên
            name = entry.get("display_name", "???")[:12]
            name_color = (255, 255, 100) if is_me else (220, 220, 220)
            name_text = self.font_small.render(name, True, name_color)
            self.screen.blit(name_text, (panel_x + 38, y))

            # Điểm
            score_text = self.font_small.render(str(entry.get("score", 0)), True, (100, 255, 100))
            self.screen.blit(score_text, (panel_x + panel_w - 55, y))

    def draw_minimap(self, snakes: dict, my_id: str, cam_x: float, cam_y: float):
        """Vẽ radar minimap góc dưới phải."""
        map_size = 160
        map_x = self.width - map_size - 15
        map_y = self.height - map_size - 15
        scale_x = map_size / GameConfig.WORLD_WIDTH
        scale_y = map_size / GameConfig.WORLD_HEIGHT

        # Nền minimap
        map_surf = pygame.Surface((map_size, map_size), pygame.SRCALPHA)
        map_surf.fill((0, 0, 0, 160))
        pygame.draw.rect(map_surf, (100, 100, 200, 200),
                         (0, 0, map_size, map_size), 2, border_radius=6)

        # Vẽ các rắn lên minimap
        for pid, snake in snakes.items():
            sx = int(snake["x"] * scale_x)
            sy = int(snake["y"] * scale_y)
            if pid == my_id:
                # Bản thân: xanh lá, to hơn
                pygame.draw.circle(map_surf, (50, 255, 50), (sx, sy), 4)
                pygame.draw.circle(map_surf, (200, 255, 200), (sx, sy), 2)
            else:
                # Đối thủ: đỏ
                color = hex_to_rgb(snake.get("skin_color", "#FF6B6B"))
                pygame.draw.circle(map_surf, color, (sx, sy), 2)

        # Vị trí camera (viewport)
        vp_x = int(cam_x * scale_x)
        vp_y = int(cam_y * scale_y)
        vp_w = int(self.width * scale_x)
        vp_h = int(self.height * scale_y)
        pygame.draw.rect(map_surf, (255, 255, 255, 100),
                         (vp_x, vp_y, vp_w, vp_h), 1)

        self.screen.blit(map_surf, (map_x, map_y))

        # Label
        label = self.font_small.render("MINIMAP", True, (150, 150, 200))
        self.screen.blit(label, (map_x + map_size//2 - label.get_width()//2, map_y - 16))

    def draw_chat(self, messages: list):
        """Vẽ khung chat góc dưới trái."""
        if not messages:
            return
        max_msgs = 8
        msgs = messages[-max_msgs:]
        line_h = 20
        panel_w = 380
        panel_h = len(msgs) * line_h + 10
        panel_x = 15
        panel_y = self.height - panel_h - 15

        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 130))
        self.screen.blit(bg, (panel_x, panel_y))

        for i, msg in enumerate(msgs):
            sender = msg.get("sender", "")
            text = msg.get("message", "")
            full = f"{sender}: {text}" if sender else text
            alpha = 255 if i == len(msgs) - 1 else max(100, 255 - (len(msgs) - 1 - i) * 30)

            if "System" in sender or "🎮" in sender:
                col = (255, 180, 80)
            elif "💀" in text or "bị" in text:
                col = (255, 100, 100)
            else:
                col = (220, 220, 220)

            surf = self.font_small.render(full[:55], True, col)
            surf.set_alpha(alpha)
            self.screen.blit(surf, (panel_x + 5, panel_y + 5 + i * line_h))

    # -------------------------
    # VẼ MÀN HÌNH GAME OVER
    # -------------------------

    def draw_game_over(self, score: int, length: int, kills: int,
                       time_alive: int, rank: int, total: int):
        """Màn hình thông báo rắn chết."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Panel giữa màn hình
        panel_w, panel_h = 450, 380
        panel_x = (self.width - panel_w) // 2
        panel_y = (self.height - panel_h) // 2

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((20, 20, 60, 220))
        pygame.draw.rect(panel, (255, 80, 80, 200), (0, 0, panel_w, panel_h), 3, border_radius=15)
        self.screen.blit(panel, (panel_x, panel_y))

        # Tiêu đề
        pulse = 0.7 + 0.3 * math.sin(self.anim_time * 3)
        r = int(255 * pulse)
        title = self.font_xlarge.render("💥 RẮN ĐÃ NỔ XÁC!", True, (r, 80, 80))
        self.screen.blit(title, (panel_x + panel_w//2 - title.get_width()//2, panel_y + 20))

        # Thống kê
        stats = [
            ("🏆 Điểm số", f"{score:,}", (255, 220, 50)),
            ("🐍 Chiều dài", str(length), (100, 220, 100)),
            ("💀 Tiêu diệt", str(kills), (255, 120, 120)),
            ("⏱️  Thời gian sống", f"{time_alive}s", (100, 180, 255)),
            ("📊 Xếp hạng", f"#{rank} / {total}", (200, 150, 255)),
        ]

        for i, (label, value, col) in enumerate(stats):
            y = panel_y + 90 + i * 48
            lbl_surf = self.font_large.render(label, True, (180, 180, 180))
            val_surf = self.font_large.render(value, True, col)
            self.screen.blit(lbl_surf, (panel_x + 30, y))
            self.screen.blit(val_surf, (panel_x + panel_w - val_surf.get_width() - 30, y))
            # Dòng kẻ
            pygame.draw.line(self.screen, (60, 60, 100),
                             (panel_x + 20, y + 36), (panel_x + panel_w - 20, y + 36), 1)

        # Hướng dẫn
        hint = self.font_medium.render("[ SPACE ] Hồi sinh    [ ESC ] Thoát phòng", True, (150, 150, 200))
        self.screen.blit(hint, (panel_x + panel_w//2 - hint.get_width()//2, panel_y + panel_h - 40))

    # -------------------------
    # VẼ LOADING / CONNECTION
    # -------------------------

    def draw_loading(self, message: str = "Đang kết nối..."):
        """Màn hình loading."""
        self.screen.fill((8, 10, 25))
        # Spinner animation
        n_dots = 12
        for i in range(n_dots):
            angle = (i / n_dots) * math.pi * 2 + self.anim_time * 3
            r = 40
            x = self.width // 2 + int(math.cos(angle) * r)
            y = self.height // 2 + int(math.sin(angle) * r)
            alpha = int(255 * ((i + self.anim_time * n_dots) % n_dots) / n_dots)
            pygame.draw.circle(self.screen, (100, 150, 255), (x, y), 5)

        text = self.font_large.render(message, True, (200, 200, 255))
        self.screen.blit(text, (self.width//2 - text.get_width()//2, self.height//2 + 70))
