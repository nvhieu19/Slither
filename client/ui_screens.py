# =============================================================================
# client/ui_screens.py - Các màn hình giao diện (Menu, Login, Lobby, ...)
# Môn: Lập Trình Mạng | Game Rắn Săn Mồi Multiplayer
# =============================================================================

import pygame
try:
    import pygame.scrap as pygame_scrap
except ImportError:
    pygame_scrap = None
import math
import random
import time
from client.renderer import hex_to_rgb, darken, lighten

# Bảng màu skin có sẵn (36 màu)
SKIN_COLORS = [
    "#FF6B6B", "#FF8E53", "#FFD93D", "#6BCB77", "#4D96FF",
    "#9B59B6", "#1ABC9C", "#E74C3C", "#F39C12", "#2ECC71",
    "#3498DB", "#8E44AD", "#16A085", "#D35400", "#C0392B",
    "#27AE60", "#2980B9", "#7F8C8D", "#E91E63", "#FF5722",
    "#4CAF50", "#00BCD4", "#673AB7", "#FF9800", "#795548",
    "#607D8B", "#F44336", "#9C27B0", "#03A9F4", "#8BC34A",
    "#FFEB3B", "#FFC107", "#00E5FF", "#76FF03", "#FF6D00",
    "#EA80FC",
]


class UIColors:
    """Bảng màu giao diện."""
    BG_DARK    = (8, 10, 25)
    BG_PANEL   = (18, 22, 55)
    BORDER     = (80, 100, 200)
    BORDER_HL  = (140, 160, 255)
    TEXT_WHITE = (230, 230, 255)
    TEXT_GRAY  = (140, 140, 180)
    TEXT_GREEN = (80, 220, 100)
    TEXT_RED   = (255, 100, 100)
    TEXT_GOLD  = (255, 215, 50)
    BTN_NORMAL = (40, 60, 160)
    BTN_HOVER  = (70, 100, 220)
    BTN_PRESS  = (20, 40, 120)
    INPUT_BG   = (15, 18, 45)
    INPUT_ACT  = (25, 30, 70)
    GREEN_BTN  = (30, 130, 60)
    GREEN_HL   = (50, 180, 90)
    RED_BTN    = (130, 30, 30)
    RED_HL     = (180, 50, 50)


def draw_panel(surface: pygame.Surface, x: int, y: int, w: int, h: int,
               bg=UIColors.BG_PANEL, border=UIColors.BORDER, radius: int = 12, alpha: int = 220):
    """Vẽ panel bo góc với nền trong suốt."""
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    panel.fill((*bg, alpha))
    pygame.draw.rect(panel, (*border, 220), (0, 0, w, h), 2, border_radius=radius)
    surface.blit(panel, (x, y))


def draw_button(surface: pygame.Surface, font: pygame.font.Font,
                text: str, x: int, y: int, w: int, h: int,
                is_hover: bool = False, is_press: bool = False,
                color=None, text_color=UIColors.TEXT_WHITE,
                radius: int = 10) -> pygame.Rect:
    """Vẽ nút bấm và trả về Rect để kiểm tra click."""
    if color is None:
        if is_press:
            bg = UIColors.BTN_PRESS
        elif is_hover:
            bg = UIColors.BTN_HOVER
        else:
            bg = UIColors.BTN_NORMAL
    else:
        bg = color

    rect = pygame.Rect(x, y, w, h)
    btn_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    btn_surf.fill((*bg, 220))

    # Viền gradient
    border_color = UIColors.BORDER_HL if is_hover else UIColors.BORDER
    pygame.draw.rect(btn_surf, (*border_color, 200), (0, 0, w, h), 2, border_radius=radius)

    # Highlight trên cùng
    hl_color = (*lighten(bg, 1.5), 80)
    pygame.draw.rect(btn_surf, hl_color, (2, 2, w-4, h//3), border_radius=radius)

    surface.blit(btn_surf, (x, y))

    txt_surf = font.render(text, True, text_color)
    surface.blit(txt_surf, (x + w//2 - txt_surf.get_width()//2,
                             y + h//2 - txt_surf.get_height()//2))
    return rect


class InputBox:
    """Ô nhập liệu có style."""

    def __init__(self, x: int, y: int, w: int, h: int,
                 placeholder: str = "", password: bool = False,
                 font: pygame.font.Font = None, max_len: int = 50):
        self.rect = pygame.Rect(x, y, w, h)
        self.placeholder = placeholder
        self.password = password
        self.font = font or pygame.font.SysFont(None, 20)
        self.max_len = max_len
        self.text = ""
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Xử lý event. Trả về text nếu nhấn Enter."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            was_active = self.active
            self.active = self.rect.collidepoint(event.pos)
            if self.active and not was_active:
                if hasattr(pygame.key, "start_text_input"):
                    try:
                        pygame.key.start_text_input()
                    except Exception:
                        pass

        elif self.active:
            # Xử lý nhập text qua sự kiện TEXTINPUT của Pygame (hỗ trợ Unicode / bộ gõ tiếng Việt)
            if hasattr(pygame, "TEXTINPUT") and event.type == pygame.TEXTINPUT:
                if len(self.text) + len(event.text) <= self.max_len:
                    self.text += event.text
                return None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return self.text
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.key == pygame.K_v and (event.mod & pygame.KMOD_CTRL):
                    if pygame_scrap:
                        try:
                            if not pygame_scrap.get_init():
                                pygame_scrap.init()
                            clip = pygame_scrap.get(pygame.SCRAP_TEXT)
                            if clip:
                                clip_text = clip.decode("utf-8", errors="ignore").rstrip("\x00")
                                self.text = (self.text + clip_text)[:self.max_len]
                        except Exception:
                            pass
                elif not hasattr(pygame, "TEXTINPUT"):
                    # Fallback cho phiên bản pygame cũ không có TEXTINPUT
                    if len(self.text) < self.max_len and event.unicode.isprintable():
                        self.text += event.unicode
        return None

    def draw(self, surface: pygame.Surface):
        """Vẽ ô nhập liệu."""
        bg = UIColors.INPUT_ACT if self.active else UIColors.INPUT_BG
        border = UIColors.BORDER_HL if self.active else UIColors.BORDER

        pygame.draw.rect(surface, bg, self.rect, border_radius=8)
        pygame.draw.rect(surface, border, self.rect, 2, border_radius=8)

        # Text hoặc placeholder
        if self.text:
            display = ("●" * len(self.text)) if self.password else self.text
            txt = self.font.render(display, True, UIColors.TEXT_WHITE)
        else:
            txt = self.font.render(self.placeholder, True, UIColors.TEXT_GRAY)

        surface.blit(txt, (self.rect.x + 10,
                            self.rect.y + self.rect.height // 2 - txt.get_height() // 2))

        # Cursor nhấp nháy
        if self.active:
            self.cursor_timer += 1
            if self.cursor_timer >= 30:
                self.cursor_timer = 0
                self.cursor_visible = not self.cursor_visible

            if self.cursor_visible and self.text:
                display_text = ("●" * len(self.text)) if self.password else self.text
                tw = self.font.size(display_text)[0]
                cx = self.rect.x + 10 + tw + 2
                cy = self.rect.y + 6
                pygame.draw.line(surface, UIColors.TEXT_WHITE,
                                 (cx, cy), (cx, cy + self.rect.height - 12), 2)


# =============================================================================
# MÀN HÌNH CHÍNH (MAIN MENU)
# =============================================================================

class MainMenuScreen:
    """Màn hình menu chính với animation rắn chạy nền."""

    def __init__(self, screen: pygame.Surface, fonts: dict):
        self.screen = screen
        self.fonts = fonts
        self.w = screen.get_width()
        self.h = screen.get_height()
        self.t = 0.0

        # Các con rắn trang trí chạy nền
        self.deco_snakes = self._create_deco_snakes()

        # Buttons
        self.buttons = {}
        self.hovered = None

    def _create_deco_snakes(self) -> list:
        """Tạo rắn trang trí chạy nền."""
        snakes = []
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD"]
        for i in range(6):
            snakes.append({
                "x": random.uniform(0, self.w),
                "y": random.uniform(0, self.h),
                "angle": random.uniform(0, 2 * math.pi),
                "color": colors[i % len(colors)],
                "history": [],
                "speed": random.uniform(1.5, 3.0),
                "length": random.randint(40, 80),
            })
        return snakes

    def _update_deco_snakes(self):
        """Di chuyển rắn trang trí."""
        for s in self.deco_snakes:
            # Xoay nhẹ theo thời gian
            s["angle"] += math.sin(self.t * 0.5 + s["x"] * 0.01) * 0.03

            new_x = s["x"] + math.cos(s["angle"]) * s["speed"]
            new_y = s["y"] + math.sin(s["angle"]) * s["speed"]

            # Wrap around
            new_x %= self.w
            new_y %= self.h
            s["x"] = new_x
            s["y"] = new_y
            s["history"].insert(0, (new_x, new_y))
            if len(s["history"]) > s["length"]:
                s["history"].pop()

    def _draw_deco_snakes(self):
        """Vẽ rắn trang trí."""
        for s in self.deco_snakes:
            history = s["history"]
            color = hex_to_rgb(s["color"])
            n = len(history)
            for i, (x, y) in enumerate(history):
                t = i / max(n - 1, 1)
                r = max(2, int(8 * (1 - t * 0.6)))
                alpha = int(180 * (1 - t))
                c = tuple(int(c * (1 - t * 0.5)) for c in color)
                pygame.draw.circle(self.screen, c, (int(x), int(y)), r)

    def update(self, dt: float = 1/60):
        self.t += dt
        self._update_deco_snakes()

    def draw(self, error_msg: str = ""):
        """Vẽ màn hình menu."""
        # Nền
        self.screen.fill(UIColors.BG_DARK)

        # Rắn trang trí
        self._draw_deco_snakes()

        # Overlay tối nền
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 120))
        self.screen.blit(overlay, (0, 0))

        # Logo / Title
        pulse = 0.9 + 0.1 * math.sin(self.t * 2)
        logo_color = (
            int(80 + 175 * pulse),
            int(50 + 50 * math.sin(self.t * 1.5)),
            int(200 + 55 * math.cos(self.t))
        )

        title1 = self.fonts["xlarge"].render("🐍 SLITHER.IO", True, logo_color)
        title2 = self.fonts["large"].render("MULTIPLAYER SNAKE BATTLE", True, (150, 150, 220))
        subtitle = self.fonts["medium"].render("Game Rắn Săn Mồi Nhiều Người Chơi", True, (120, 120, 180))

        # Shadow logo
        shadow = self.fonts["xlarge"].render("🐍 SLITHER.IO", True, (0, 0, 0))
        self.screen.blit(shadow, (self.w//2 - shadow.get_width()//2 + 3, self.h//4 - 30 + 3))
        self.screen.blit(title1, (self.w//2 - title1.get_width()//2, self.h//4 - 30))
        self.screen.blit(title2, (self.w//2 - title2.get_width()//2, self.h//4 + 40))
        self.screen.blit(subtitle, (self.w//2 - subtitle.get_width()//2, self.h//4 + 70))

        # Buttons
        btn_w, btn_h = 260, 52
        btn_x = self.w // 2 - btn_w // 2
        buttons_config = [
            ("🔑 ĐĂNG NHẬP",   "login",    UIColors.BTN_NORMAL),
            ("📝 ĐĂNG KÝ",     "register", UIColors.GREEN_BTN),
            ("🏆 BẢNG XẾP HẠNG", "leaderboard", (60, 60, 120)),
            ("❌ THOÁT",       "quit",     UIColors.RED_BTN),
        ]

        mouse_pos = pygame.mouse.get_pos()
        self.buttons = {}

        for i, (label, key, color) in enumerate(buttons_config):
            by = self.h // 2 + 20 + i * 65
            is_hover = pygame.Rect(btn_x, by, btn_w, btn_h).collidepoint(mouse_pos)
            rect = draw_button(self.screen, self.fonts["large"], label,
                               btn_x, by, btn_w, btn_h,
                               is_hover=is_hover, color=color if not is_hover else lighten(color, 1.3))
            self.buttons[key] = rect

        # Error message
        if error_msg:
            err_surf = self.fonts["medium"].render(error_msg, True, UIColors.TEXT_RED)
            ey = self.h // 2 + 10
            self.screen.blit(err_surf, (self.w//2 - err_surf.get_width()//2, ey))

        # Version
        ver = self.fonts["small"].render("v1.0 | Lập Trình Mạng 2024", True, (80, 80, 120))
        self.screen.blit(ver, (10, self.h - 25))

    def handle_click(self, pos: tuple) -> str | None:
        for key, rect in self.buttons.items():
            if rect.collidepoint(pos):
                return key
        return None


# =============================================================================
# MÀN HÌNH ĐĂNG NHẬP / ĐĂNG KÝ
# =============================================================================

class AuthScreen:
    """Màn hình đăng nhập hoặc đăng ký."""

    def __init__(self, screen: pygame.Surface, fonts: dict, mode: str = "login"):
        self.screen = screen
        self.fonts = fonts
        self.mode = mode  # "login" hoặc "register"
        self.w = screen.get_width()
        self.h = screen.get_height()
        self.t = 0.0

        self.message = ""
        self.message_color = UIColors.TEXT_RED
        self.loading = False

        # Panel
        self.panel_w, self.panel_h = 440, 420 if mode == "register" else 360
        self.panel_x = (self.w - self.panel_w) // 2
        self.panel_y = (self.h - self.panel_h) // 2

        # Input boxes
        ix = self.panel_x + 30
        iw = self.panel_w - 60

        self.inputs = {}
        if mode == "register":
            self.inputs["display_name"] = InputBox(ix, self.panel_y + 105, iw, 40,
                                                   "Tên hiển thị (Display Name)", font=fonts["medium"])
        self.inputs["username"] = InputBox(ix, self.panel_y + (155 if mode == "register" else 105), iw, 40,
                                           "Tên đăng nhập (Username)", font=fonts["medium"])
        self.inputs["password"] = InputBox(ix, self.panel_y + (215 if mode == "register" else 165), iw, 40,
                                           "Mật khẩu (Password)", password=True, font=fonts["medium"])

        self.buttons = {}
        self.active_input = None

    def update(self, dt: float = 1/60):
        self.t += dt

    def draw(self):
        # Nền
        self.screen.fill(UIColors.BG_DARK)

        # Hiệu ứng nền động
        for i in range(5):
            phase = self.t + i * 1.2
            cx = int(self.w * (0.2 + 0.6 * ((math.sin(phase * 0.3) + 1) / 2)))
            cy = int(self.h * (0.2 + 0.6 * ((math.cos(phase * 0.4) + 1) / 2)))
            r = int(80 + 40 * math.sin(phase))
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            colors = [(80, 30, 150), (20, 100, 180), (150, 50, 50), (20, 130, 80), (100, 80, 30)]
            pygame.draw.circle(s, (*colors[i % len(colors)], 25), (r, r), r)
            self.screen.blit(s, (cx - r, cy - r))

        # Panel chính
        draw_panel(self.screen, self.panel_x, self.panel_y,
                   self.panel_w, self.panel_h, radius=15, alpha=230)

        # Tiêu đề
        title = "📝 ĐĂNG KÝ TÀI KHOẢN" if self.mode == "register" else "🔑 ĐĂNG NHẬP"
        t_surf = self.fonts["xlarge"].render(title, True, UIColors.TEXT_WHITE)
        self.screen.blit(t_surf, (self.panel_x + self.panel_w//2 - t_surf.get_width()//2,
                                  self.panel_y + 20))

        # Subtitle
        sub = "Tạo tài khoản để bắt đầu chơi" if self.mode == "register" else "Chào mừng trở lại!"
        s_surf = self.fonts["medium"].render(sub, True, UIColors.TEXT_GRAY)
        self.screen.blit(s_surf, (self.panel_x + self.panel_w//2 - s_surf.get_width()//2,
                                  self.panel_y + 65))

        # Input labels + boxes
        labels = {
            "display_name": "👤 Tên hiển thị:",
            "username": "📧 Tên đăng nhập:",
            "password": "🔒 Mật khẩu:"
        }
        for key, inp in self.inputs.items():
            lbl = self.fonts["small"].render(labels.get(key, key), True, UIColors.TEXT_GRAY)
            self.screen.blit(lbl, (inp.rect.x, inp.rect.y - 18))
            inp.draw(self.screen)

        # Buttons
        btn_y_base = self.panel_y + (285 if self.mode == "register" else 235)
        mouse_pos = pygame.mouse.get_pos()

        main_text = "📝 Đăng ký" if self.mode == "register" else "🔑 Đăng nhập"
        main_rect = pygame.Rect(self.panel_x + 30, btn_y_base, self.panel_w - 60, 48)
        is_hover = main_rect.collidepoint(mouse_pos)
        color = UIColors.GREEN_BTN if self.mode == "register" else UIColors.BTN_NORMAL
        hover_col = UIColors.GREEN_HL if self.mode == "register" else UIColors.BTN_HOVER
        draw_button(self.screen, self.fonts["large"], main_text,
                    main_rect.x, main_rect.y, main_rect.w, main_rect.h,
                    is_hover=is_hover, color=hover_col if is_hover else color)
        self.buttons["submit"] = main_rect

        back_rect = pygame.Rect(self.panel_x + 30, btn_y_base + 58, self.panel_w - 60, 40)
        is_hover_back = back_rect.collidepoint(mouse_pos)
        draw_button(self.screen, self.fonts["medium"], "← Quay lại",
                    back_rect.x, back_rect.y, back_rect.w, back_rect.h,
                    is_hover=is_hover_back, color=(40, 40, 80))
        self.buttons["back"] = back_rect

        # Message
        if self.message:
            msg = self.fonts["medium"].render(self.message, True, self.message_color)
            self.screen.blit(msg, (self.panel_x + self.panel_w//2 - msg.get_width()//2,
                                   btn_y_base + 108))

        # Loading spinner
        if self.loading:
            spin_text = self.fonts["medium"].render(
                "⏳ " + "." * (int(self.t * 4) % 4 + 1), True, (150, 200, 255))
            self.screen.blit(spin_text, (self.panel_x + self.panel_w//2 - spin_text.get_width()//2,
                                         btn_y_base + 130))

    def handle_event(self, event: pygame.event.Event) -> dict | None:
        """Trả về {"action": str, "data": dict} hoặc None."""
        for key, inp in self.inputs.items():
            result = inp.handle_event(event)
            if result is not None and key == "password":
                # Nhấn Enter trong ô mật khẩu = submit
                return self._get_submit_data()

        if event.type == pygame.MOUSEBUTTONDOWN:
            for key, rect in self.buttons.items():
                if rect.collidepoint(event.pos):
                    if key == "submit":
                        return self._get_submit_data()
                    elif key == "back":
                        return {"action": "back"}
        return None

    def _get_submit_data(self) -> dict:
        data = {key: inp.text for key, inp in self.inputs.items()}
        return {"action": self.mode, "data": data}

    def set_message(self, msg: str, success: bool = False):
        self.message = msg
        self.message_color = UIColors.TEXT_GREEN if success else UIColors.TEXT_RED
        self.loading = False


# =============================================================================
# MÀN HÌNH LOBBY (DANH SÁCH PHÒNG)
# =============================================================================

class LobbyScreen:
    """Màn hình sảnh chính: danh sách phòng, skin customizer."""

    def __init__(self, screen: pygame.Surface, fonts: dict, player_info: dict):
        self.screen = screen
        self.fonts = fonts
        self.w = screen.get_width()
        self.h = screen.get_height()
        self.t = 0.0
        self.player_info = player_info
        self.rooms: list = []
        self.selected_room: str | None = None
        self.scroll_offset = 0
        self.tab = "rooms"  # "rooms" | "skin"
        self.buttons = {}
        self.selected_skin = player_info.get("skin_color", "#4ECDC4")
        self.message = ""
        self.msg_timer = 0

        # Input tên phòng
        self.room_name_input = InputBox(
            self.w // 2 - 160, self.h - 90, 220, 38,
            "Tên phòng...", font=fonts["medium"], max_len=30
        )
        self.creating_room = False

    def update(self, dt: float = 1/60):
        self.t += dt
        if self.msg_timer > 0:
            self.msg_timer -= 1

    def draw(self):
        self.screen.fill(UIColors.BG_DARK)
        # Animated background
        for i in range(3):
            r = int(300 + 100 * math.sin(self.t * 0.4 + i))
            cx = int(self.w * (0.2 + 0.6 * i / 2))
            cy = self.h // 2
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (20, 30, 80, 20), (r, r), r)
            self.screen.blit(s, (cx - r, cy - r))

        self._draw_header()
        self._draw_tabs()

        if self.tab == "rooms":
            self._draw_room_list()
        elif self.tab == "skin":
            self._draw_skin_selector()

        # Message
        if self.msg_timer > 0 and self.message:
            m = self.fonts["medium"].render(self.message, True, UIColors.TEXT_GREEN)
            self.screen.blit(m, (self.w//2 - m.get_width()//2, self.h - 30))

    def _draw_header(self):
        """Header với thông tin người chơi."""
        draw_panel(self.screen, 0, 0, self.w, 55, bg=(10, 15, 40), radius=0, alpha=230)

        # Avatar (hình tròn màu skin)
        skin_color = hex_to_rgb(self.player_info.get("skin_color", "#4ECDC4"))
        pygame.draw.circle(self.screen, skin_color, (35, 27), 18)
        pygame.draw.circle(self.screen, (200, 200, 255), (35, 27), 18, 2)

        # Tên người chơi
        name = self.player_info.get("display_name", "Player")
        n_surf = self.fonts["large"].render(f"👤 {name}", True, UIColors.TEXT_WHITE)
        self.screen.blit(n_surf, (65, 10))

        # Điểm cao nhất
        best = self.player_info.get("highest_score", 0)
        s_surf = self.fonts["medium"].render(f"🏆 Kỷ lục: {best}", True, UIColors.TEXT_GOLD)
        self.screen.blit(s_surf, (65, 35))

        # Nút logout
        mouse_pos = pygame.mouse.get_pos()
        lr = pygame.Rect(self.w - 130, 10, 120, 36)
        is_hover = lr.collidepoint(mouse_pos)
        draw_button(self.screen, self.fonts["medium"], "🚪 Đăng xuất",
                    lr.x, lr.y, lr.w, lr.h,
                    is_hover=is_hover, color=UIColors.RED_BTN if not is_hover else UIColors.RED_HL)
        self.buttons["logout"] = lr

    def _draw_tabs(self):
        """Tab chuyển đổi."""
        tabs = [("🏠 Danh sách phòng", "rooms"), ("🎨 Tùy chỉnh Skin", "skin")]
        tw = 200
        for i, (label, key) in enumerate(tabs):
            tx = 20 + i * (tw + 10)
            ty = 62
            is_active = self.tab == key
            color = UIColors.BTN_HOVER if is_active else UIColors.BTN_NORMAL
            rect = draw_button(self.screen, self.fonts["medium"], label,
                               tx, ty, tw, 36,
                               is_hover=is_active, color=color)
            self.buttons[f"tab_{key}"] = rect

    def _draw_room_list(self):
        """Danh sách phòng có thể scroll."""
        list_x, list_y = 20, 110
        list_w, list_h = self.w - 300, self.h - 200
        item_h = 70

        draw_panel(self.screen, list_x, list_y, list_w, list_h, alpha=180)

        # Header
        header = self.fonts["medium"].render(
            f"📋 Có {len(self.rooms)} phòng đang mở", True, UIColors.TEXT_WHITE)
        self.screen.blit(header, (list_x + 10, list_y + 8))

        # Clip vùng vẽ
        clip_rect = pygame.Rect(list_x + 2, list_y + 35, list_w - 4, list_h - 40)
        self.screen.set_clip(clip_rect)

        mouse_pos = pygame.mouse.get_pos()

        if not self.rooms:
            no_room = self.fonts["large"].render("Chưa có phòng nào. Hãy tạo phòng mới!", True, UIColors.TEXT_GRAY)
            self.screen.blit(no_room, (list_x + list_w//2 - no_room.get_width()//2,
                                        list_y + list_h//2 - 20))
        else:
            for i, room in enumerate(self.rooms):
                ry = list_y + 40 + i * (item_h + 5) - self.scroll_offset
                if ry + item_h < list_y or ry > list_y + list_h:
                    continue

                is_selected = room.get("room_id") == self.selected_room
                is_hover = pygame.Rect(list_x + 5, ry, list_w - 10, item_h).collidepoint(mouse_pos)
                bg_color = (50, 80, 160) if is_selected else ((30, 50, 110) if is_hover else (20, 30, 70))

                draw_panel(self.screen, list_x + 5, ry, list_w - 10, item_h,
                           bg=bg_color, radius=8, alpha=200)

                # Status badge
                status = room.get("status", "WAITING")
                st_color = UIColors.TEXT_GREEN if status == "WAITING" else (255, 150, 50)
                st_text = "🟢 Đang chờ" if status == "WAITING" else "🔴 Đang chơi"
                st_surf = self.fonts["small"].render(st_text, True, st_color)
                self.screen.blit(st_surf, (list_x + 15, ry + 5))

                # Tên phòng
                name_surf = self.fonts["large"].render(
                    room.get("room_name", f"Phòng {i+1}"), True, UIColors.TEXT_WHITE)
                self.screen.blit(name_surf, (list_x + 15, ry + 23))

                # Thông tin
                info = f"👑 {room.get('host', '?')}  |  👥 {room.get('players', 0)}/{room.get('max_players', 10)}"
                info_surf = self.fonts["small"].render(info, True, UIColors.TEXT_GRAY)
                self.screen.blit(info_surf, (list_x + 15, ry + 48))

                # ID
                id_surf = self.fonts["small"].render(
                    f"ID: {room.get('room_id', '?')}", True, (80, 80, 120))
                self.screen.blit(id_surf, (list_x + list_w - id_surf.get_width() - 20, ry + 5))

                # Nút vào
                if status == "WAITING":
                    join_r = pygame.Rect(list_x + list_w - 100, ry + 20, 90, 32)
                    is_join_hover = join_r.collidepoint(mouse_pos)
                    draw_button(self.screen, self.fonts["small"], "▶ Vào phòng",
                                join_r.x, join_r.y, join_r.w, join_r.h,
                                is_hover=is_join_hover, color=UIColors.GREEN_BTN if not is_join_hover else UIColors.GREEN_HL)
                    self.buttons[f"join_{room.get('room_id')}"] = join_r

        self.screen.set_clip(None)

        # Bảng phải: tạo phòng & nút refresh
        side_x = list_x + list_w + 10
        side_w = self.w - side_x - 15
        draw_panel(self.screen, side_x, list_y, side_w, list_h, alpha=180)

        title = self.fonts["large"].render("➕ TẠO PHÒNG MỚI", True, UIColors.TEXT_WHITE)
        self.screen.blit(title, (side_x + 10, list_y + 10))

        lbl = self.fonts["small"].render("Tên phòng:", True, UIColors.TEXT_GRAY)
        self.screen.blit(lbl, (side_x + 10, list_y + 50))

        # Cập nhật vị trí input tên phòng
        self.room_name_input.rect.x = side_x + 10
        self.room_name_input.rect.y = list_y + 70
        self.room_name_input.rect.w = side_w - 20
        self.room_name_input.draw(self.screen)

        create_r = pygame.Rect(side_x + 10, list_y + 120, side_w - 20, 44)
        is_hover = create_r.collidepoint(mouse_pos)
        draw_button(self.screen, self.fonts["large"], "🏠 Tạo Phòng",
                    create_r.x, create_r.y, create_r.w, create_r.h,
                    is_hover=is_hover, color=UIColors.GREEN_BTN if not is_hover else UIColors.GREEN_HL)
        self.buttons["create_room"] = create_r

        refresh_r = pygame.Rect(side_x + 10, list_y + 175, side_w - 20, 40)
        is_hover_r = refresh_r.collidepoint(mouse_pos)
        draw_button(self.screen, self.fonts["medium"], "🔄 Làm mới",
                    refresh_r.x, refresh_r.y, refresh_r.w, refresh_r.h,
                    is_hover=is_hover_r, color=(40, 60, 120))
        self.buttons["refresh"] = refresh_r

        lboard_r = pygame.Rect(side_x + 10, list_y + 225, side_w - 20, 40)
        is_hover_l = lboard_r.collidepoint(mouse_pos)
        draw_button(self.screen, self.fonts["medium"], "🏆 BXH Tổng",
                    lboard_r.x, lboard_r.y, lboard_r.w, lboard_r.h,
                    is_hover=is_hover_l, color=(60, 40, 120))
        self.buttons["leaderboard"] = lboard_r

    def _draw_skin_selector(self):
        """Bộ chọn màu skin."""
        panel_x, panel_y = 20, 110
        panel_w, panel_h = self.w - 40, self.h - 160

        draw_panel(self.screen, panel_x, panel_y, panel_w, panel_h, alpha=200)

        title = self.fonts["xlarge"].render("🎨 TÙY CHỈNH SKIN RẮN", True, UIColors.TEXT_WHITE)
        self.screen.blit(title, (panel_x + panel_w//2 - title.get_width()//2, panel_y + 12))

        # Preview rắn với màu hiện tại
        preview_color = hex_to_rgb(self.selected_skin)
        preview_x = panel_x + panel_w//2
        preview_y = panel_y + 80
        # Vẽ thân rắn mẫu
        for i in range(20):
            px = preview_x - i * 12 + 120
            py = preview_y + int(20 * math.sin(i * 0.5 + self.t * 2))
            r = max(4, 12 - i // 3)
            t_val = i / 20
            seg_c = tuple(int(c * (1 - t_val * 0.5)) for c in preview_color)
            pygame.draw.circle(self.screen, seg_c, (px, py), r)
        # Đầu
        pygame.draw.circle(self.screen, preview_color, (preview_x + 120, preview_y), 14)
        pygame.draw.circle(self.screen, (240, 240, 240), (preview_x + 125, preview_y - 4), 4)
        pygame.draw.circle(self.screen, (20, 20, 20), (preview_x + 125, preview_y - 4), 2)

        # Mã màu hiện tại
        hex_text = self.fonts["large"].render(f"Màu: {self.selected_skin}", True, preview_color)
        self.screen.blit(hex_text, (panel_x + panel_w//2 - hex_text.get_width()//2, panel_y + 115))

        # Grid chọn màu
        cols = 12
        swatch_size = 42
        start_x = panel_x + (panel_w - cols * (swatch_size + 6)) // 2
        start_y = panel_y + 150

        mouse_pos = pygame.mouse.get_pos()
        for idx, color_hex in enumerate(SKIN_COLORS):
            col = idx % cols
            row = idx // cols
            sx = start_x + col * (swatch_size + 6)
            sy = start_y + row * (swatch_size + 6)
            sr = pygame.Rect(sx, sy, swatch_size, swatch_size)

            color = hex_to_rgb(color_hex)
            is_selected = color_hex == self.selected_skin
            is_hover = sr.collidepoint(mouse_pos)

            # Nền ô màu
            pygame.draw.rect(self.screen, color, sr, border_radius=8)
            if is_selected:
                pygame.draw.rect(self.screen, (255, 255, 255), sr, 3, border_radius=8)
                # Dấu check
                ck = self.fonts["medium"].render("✓", True, (255, 255, 255))
                self.screen.blit(ck, (sx + swatch_size//2 - ck.get_width()//2,
                                      sy + swatch_size//2 - ck.get_height()//2))
            elif is_hover:
                pygame.draw.rect(self.screen, (200, 200, 255), sr, 2, border_radius=8)

            self.buttons[f"skin_{color_hex}"] = sr

        # Nút lưu
        save_y = start_y + ((len(SKIN_COLORS) - 1) // cols + 1) * (swatch_size + 6) + 15
        save_r = pygame.Rect(panel_x + panel_w//2 - 130, save_y, 260, 50)
        is_hover_save = save_r.collidepoint(mouse_pos)
        draw_button(self.screen, self.fonts["large"], "💾 Lưu Skin",
                    save_r.x, save_r.y, save_r.w, save_r.h,
                    is_hover=is_hover_save, color=UIColors.GREEN_BTN if not is_hover_save else UIColors.GREEN_HL)
        self.buttons["save_skin"] = save_r

    def handle_event(self, event: pygame.event.Event) -> dict | None:
        """Xử lý sự kiện."""
        # Input tên phòng
        if self.tab == "rooms":
            self.room_name_input.handle_event(event)

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_offset = max(0, self.scroll_offset - event.y * 20)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for key, rect in self.buttons.items():
                if not rect.collidepoint(pos):
                    continue
                if key == "logout":
                    return {"action": "logout"}
                elif key == "refresh":
                    return {"action": "refresh"}
                elif key == "create_room":
                    name = self.room_name_input.text.strip() or f"Phòng vui"
                    return {"action": "create_room", "room_name": name}
                elif key == "leaderboard":
                    return {"action": "leaderboard"}
                elif key.startswith("join_"):
                    room_id = key[5:]
                    return {"action": "join_room", "room_id": room_id}
                elif key.startswith("tab_"):
                    self.tab = key[4:]
                elif key.startswith("skin_"):
                    self.selected_skin = key[5:]
                elif key == "save_skin":
                    return {"action": "update_skin", "skin_color": self.selected_skin}
        return None

    def show_message(self, msg: str):
        self.message = msg
        self.msg_timer = 120  # 2 giây


# =============================================================================
# MÀN HÌNH PHÒNG CHỜ (ROOM WAITING)
# =============================================================================

class RoomWaitingScreen:
    """Màn hình sảnh chờ trong phòng."""

    def __init__(self, screen: pygame.Surface, fonts: dict,
                 room_info: dict, player_info: dict):
        self.screen = screen
        self.fonts = fonts
        self.w = screen.get_width()
        self.h = screen.get_height()
        self.t = 0.0

        self.room_info = room_info
        self.player_info = player_info
        self.player_list: list = []
        self.chat_messages: list = []
        self.is_host = False

        self.buttons = {}
        self.chat_input = InputBox(
            20, self.h - 55, self.w - 310, 40,
            "Nhập tin nhắn...", font=fonts["medium"], max_len=100
        )

    def update(self, dt: float = 1/60):
        self.t += dt

    def draw(self):
        self.screen.fill(UIColors.BG_DARK)

        # Nền gradient
        for i in range(4):
            phase = self.t * 0.3 + i * 0.8
            r = 200
            cx = int(self.w * (0.1 + 0.8 * i / 3))
            cy = self.h // 2
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (15, 25, 70, 30), (r, r), r)
            self.screen.blit(s, (cx - r, cy - r))

        # Header
        draw_panel(self.screen, 0, 0, self.w, 60, bg=(10, 15, 40), radius=0)
        title = self.fonts["large"].render(
            f"🏠 Phòng: {self.room_info.get('room_name', '?')}  |  ID: {self.room_info.get('room_id', '?')}",
            True, UIColors.TEXT_WHITE)
        self.screen.blit(title, (20, 18))

        mouse_pos = pygame.mouse.get_pos()

        # Nút rời phòng
        leave_r = pygame.Rect(self.w - 140, 12, 130, 36)
        is_hover = leave_r.collidepoint(mouse_pos)
        draw_button(self.screen, self.fonts["medium"], "🚪 Rời phòng",
                    leave_r.x, leave_r.y, leave_r.w, leave_r.h,
                    is_hover=is_hover, color=UIColors.RED_BTN if not is_hover else UIColors.RED_HL)
        self.buttons["leave"] = leave_r

        # Danh sách người chơi (trái)
        list_x, list_y = 20, 70
        list_w, list_h = self.w // 2 - 30, self.h - 200

        draw_panel(self.screen, list_x, list_y, list_w, list_h, alpha=180)
        hdr = self.fonts["large"].render(
            f"👥 Người chơi ({len(self.player_list)}/{self.room_info.get('max_players', 10)})",
            True, UIColors.TEXT_WHITE)
        self.screen.blit(hdr, (list_x + 10, list_y + 10))

        for i, p in enumerate(self.player_list):
            py = list_y + 45 + i * 56
            skin_color = hex_to_rgb(p.get("skin_color", "#4ECDC4"))
            draw_panel(self.screen, list_x + 8, py, list_w - 16, 48,
                       bg=(25, 35, 80), radius=8, alpha=180)
            pygame.draw.circle(self.screen, skin_color, (list_x + 30, py + 24), 16)
            pygame.draw.circle(self.screen, (200, 200, 255), (list_x + 30, py + 24), 16, 2)
            name = p.get("display_name", p.get("username", "?"))
            name_surf = self.fonts["large"].render(name, True, UIColors.TEXT_WHITE)
            self.screen.blit(name_surf, (list_x + 55, py + 6))
            if p.get("is_host"):
                host_surf = self.fonts["small"].render("👑 Host", True, UIColors.TEXT_GOLD)
                self.screen.blit(host_surf, (list_x + 55, py + 30))

        # Chat (phải)
        chat_x = self.w // 2 + 10
        chat_y = list_y
        chat_w = self.w - chat_x - 15
        chat_h = list_h

        draw_panel(self.screen, chat_x, chat_y, chat_w, chat_h, alpha=180)
        chat_hdr = self.fonts["large"].render("💬 Chat", True, UIColors.TEXT_WHITE)
        self.screen.blit(chat_hdr, (chat_x + 10, chat_y + 10))

        # Vẽ tin nhắn
        self.screen.set_clip(pygame.Rect(chat_x + 4, chat_y + 40, chat_w - 8, chat_h - 50))
        msgs = self.chat_messages[-20:]
        for i, msg in enumerate(msgs):
            my = chat_y + chat_h - 50 - (len(msgs) - i) * 24
            sender = msg.get("sender", "")
            text = msg.get("message", "")
            full = f"{sender}: {text}" if sender else text
            col = (255, 180, 80) if "System" in sender else (220, 220, 220)
            m_surf = self.fonts["small"].render(full[:48], True, col)
            self.screen.blit(m_surf, (chat_x + 8, my))
        self.screen.set_clip(None)

        # Chat input
        self.chat_input.rect.x = chat_x
        self.chat_input.rect.y = self.h - 135
        self.chat_input.rect.w = chat_w
        self.chat_input.draw(self.screen)

        # Nút Start (chỉ host)
        if self.is_host:
            pulse = 0.85 + 0.15 * math.sin(self.t * 4)
            start_r = pygame.Rect(20, self.h - 115, self.w // 2 - 30, 55)
            is_hover_s = start_r.collidepoint(mouse_pos)
            g = int(180 * pulse)
            draw_button(self.screen, self.fonts["xlarge"], "🎮 BẮT ĐẦU GAME",
                        start_r.x, start_r.y, start_r.w, start_r.h,
                        is_hover=is_hover_s, color=(30, g, 50) if not is_hover_s else (50, 220, 80))
            self.buttons["start"] = start_r

        # Chat send button
        send_r = pygame.Rect(chat_x, self.h - 85, chat_w, 38)
        is_hover_send = send_r.collidepoint(mouse_pos)
        draw_button(self.screen, self.fonts["medium"], "📤 Gửi",
                    send_r.x, send_r.y, send_r.w, send_r.h,
                    is_hover=is_hover_send, color=(30, 80, 160))
        self.buttons["send_chat"] = send_r

    def handle_event(self, event: pygame.event.Event) -> dict | None:
        result = self.chat_input.handle_event(event)
        if result is not None:  # Enter trong chat
            msg = self.chat_input.text.strip()
            if msg:
                self.chat_input.text = ""
                return {"action": "chat", "message": msg}

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, rect in self.buttons.items():
                if rect.collidepoint(event.pos):
                    if key == "leave":
                        return {"action": "leave"}
                    elif key == "start":
                        return {"action": "start"}
                    elif key == "send_chat":
                        msg = self.chat_input.text.strip()
                        if msg:
                            self.chat_input.text = ""
                            return {"action": "chat", "message": msg}
        return None


# =============================================================================
# MÀN HÌNH BẢNG XẾP HẠNG TỔNG
# =============================================================================

class LeaderboardScreen:
    """Màn hình bảng xếp hạng tổng."""

    def __init__(self, screen: pygame.Surface, fonts: dict, data: list):
        self.screen = screen
        self.fonts = fonts
        self.w = screen.get_width()
        self.h = screen.get_height()
        self.data = data
        self.t = 0.0
        self.buttons = {}

    def update(self, dt: float = 1/60):
        self.t += dt

    def draw(self):
        self.screen.fill(UIColors.BG_DARK)

        # Nền
        for i in range(3):
            r = 250
            cx = int(self.w * (0.2 + 0.6 * i / 2))
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (80, 60, 10, 20), (r, r), r)
            self.screen.blit(s, (cx - r, self.h//2 - r))

        # Panel
        panel_w = min(700, self.w - 40)
        panel_x = (self.w - panel_w) // 2
        panel_y = 20
        panel_h = self.h - 80

        draw_panel(self.screen, panel_x, panel_y, panel_w, panel_h, alpha=210)

        # Tiêu đề
        title = self.fonts["title"].render("🏆 BẢNG XẾP HẠNG TỔNG", True, UIColors.TEXT_GOLD)
        self.screen.blit(title, (panel_x + panel_w//2 - title.get_width()//2, panel_y + 12))

        # Header cột
        hdrs = [("#", 50), ("Tên", 180), ("Điểm Cao", 140), ("Tiêu diệt", 120), ("Ván đấu", 100)]
        hx = panel_x + 20
        for h_text, h_w in hdrs:
            h_surf = self.fonts["medium"].render(h_text, True, UIColors.TEXT_GRAY)
            self.screen.blit(h_surf, (hx, panel_y + 80))
            hx += h_w

        pygame.draw.line(self.screen, UIColors.BORDER,
                         (panel_x + 10, panel_y + 100), (panel_x + panel_w - 10, panel_y + 100), 1)

        # Dữ liệu
        rank_colors = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]
        for i, entry in enumerate(self.data[:20]):
            ry = panel_y + 110 + i * 38
            if ry > panel_y + panel_h - 60:
                break

            # Nền xen kẽ
            if i % 2 == 0:
                row_bg = pygame.Surface((panel_w - 20, 35), pygame.SRCALPHA)
                row_bg.fill((255, 255, 255, 15))
                self.screen.blit(row_bg, (panel_x + 10, ry - 3))

            hx = panel_x + 20
            vals = [
                (f"#{i+1}", 50, rank_colors[i] if i < 3 else UIColors.TEXT_GRAY),
                (entry.get("display_name", entry.get("username", "?")), 180, UIColors.TEXT_WHITE),
                (f"{entry.get('highest_score', 0):,}", 140, UIColors.TEXT_GOLD),
                (str(entry.get("total_kills", 0)), 120, (255, 120, 120)),
                (str(entry.get("total_games", 0)), 100, UIColors.TEXT_GRAY),
            ]
            for val_text, val_w, val_color in vals:
                v_surf = self.fonts["medium"].render(str(val_text), True, val_color)
                self.screen.blit(v_surf, (hx, ry))
                hx += val_w

            # Medal cho top 3
            if i < 3:
                medal = ["🥇", "🥈", "🥉"][i]
                m_surf = self.fonts["medium"].render(medal, True, rank_colors[i])
                self.screen.blit(m_surf, (panel_x + panel_w - 55, ry))

        # Nút quay lại
        mouse_pos = pygame.mouse.get_pos()
        back_r = pygame.Rect(panel_x + panel_w//2 - 130, panel_y + panel_h - 55, 260, 46)
        is_hover = back_r.collidepoint(mouse_pos)
        draw_button(self.screen, self.fonts["large"], "← Quay lại",
                    back_r.x, back_r.y, back_r.w, back_r.h,
                    is_hover=is_hover, color=(40, 40, 80))
        self.buttons["back"] = back_r

    def handle_click(self, pos: tuple) -> str | None:
        for key, rect in self.buttons.items():
            if rect.collidepoint(pos):
                return key
        return None
