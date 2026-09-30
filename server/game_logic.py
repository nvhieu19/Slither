# =============================================================================
# server/game_logic.py - Logic game phía Server (Snake, Food, World State)
# Môn: Lập Trình Mạng | Game Rắn Săn Mồi Multiplayer
# =============================================================================

import math
import random
import time
from shared.protocol import GameConfig


class Food:
    """Đại diện cho 1 hạt thức ăn trên bản đồ."""

    _id_counter = 0

    def __init__(self, x: float, y: float, score: int = 1, radius: int = 6,
                 color: str = None, food_type: str = "normal"):
        Food._id_counter += 1
        self.id = Food._id_counter
        self.x = x
        self.y = y
        self.score = score
        self.radius = radius
        self.color = color or self._random_color()
        self.food_type = food_type  # "normal" hoặc "death"
        self.pulse = random.uniform(0, math.pi * 2)  # pha nhấp nháy

    @staticmethod
    def _random_color() -> str:
        colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFEAA7",
            "#DDA0DD", "#96CEB4", "#F7DC6F", "#BB8FCE",
            "#FFA07A", "#98FB98", "#87CEEB", "#FFB6C1",
        ]
        return random.choice(colors)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "score": self.score,
            "radius": self.radius,
            "color": self.color,
            "food_type": self.food_type
        }


class Snake:
    """Đại diện cho 1 con rắn trong game."""

    def __init__(self, player_id: str, username: str, display_name: str,
                 skin_color: str, start_x: float = None, start_y: float = None):
        self.player_id = player_id
        self.username = username
        self.display_name = display_name
        self.skin_color = skin_color

        # Vị trí ban đầu ngẫu nhiên (tránh rìa)
        margin = 300
        self.x = start_x or random.uniform(margin, GameConfig.WORLD_WIDTH - margin)
        self.y = start_y or random.uniform(margin, GameConfig.WORLD_HEIGHT - margin)
        self.angle = random.uniform(0, math.pi * 2)

        # Mảng lịch sử tọa độ để vẽ thân rắn
        # Mỗi phần tử là (x, y), trải đều phía sau đầu rắn theo hướng ngược lại
        segment_spacing = GameConfig.SNAKE_SEGMENT_DIST
        self.history = [
            (self.x - math.cos(self.angle) * segment_spacing * i,
             self.y - math.sin(self.angle) * segment_spacing * i)
            for i in range(GameConfig.INITIAL_LENGTH)
        ]

        self.speed = GameConfig.SNAKE_SPEED
        self.is_boosting = False
        self.boost_timer = 0

        # Điểm số & thống kê
        self.score = 0
        self.kills = 0
        self.max_length = GameConfig.INITIAL_LENGTH
        self.alive = True
        self.start_time = time.time()

        # Trạng thái input
        self.target_angle = self.angle

    @property
    def length(self) -> int:
        return len(self.history)

    def update(self, dt: float = 1.0):
        """Cập nhật vị trí rắn theo 1 tick."""
        if not self.alive:
            return

        # Xoay mượt về target_angle
        angle_diff = self.target_angle - self.angle
        # Normalize về [-pi, pi]
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        max_turn = 0.1  # radian/frame
        if abs(angle_diff) > max_turn:
            self.angle += max_turn * (1 if angle_diff > 0 else -1)
        else:
            self.angle = self.target_angle

        # Tính tốc độ hiện tại
        current_speed = GameConfig.SNAKE_BOOST_SPEED if self.is_boosting else GameConfig.SNAKE_SPEED

        # Di chuyển đầu rắn
        new_x = self.x + math.cos(self.angle) * current_speed
        new_y = self.y + math.sin(self.angle) * current_speed

        # Giới hạn trong bản đồ
        r = GameConfig.SNAKE_RADIUS
        new_x = max(r, min(GameConfig.WORLD_WIDTH - r, new_x))
        new_y = max(r, min(GameConfig.WORLD_HEIGHT - r, new_y))

        self.x = new_x
        self.y = new_y

        # Chèn đầu vào mảng history
        self.history.insert(0, (self.x, self.y))

        # Boost tiêu tốn thân
        if self.is_boosting:
            self.boost_timer += 1
            if self.boost_timer >= GameConfig.BOOST_COST_INTERVAL:
                self.boost_timer = 0
                if len(self.history) > GameConfig.INITIAL_LENGTH:
                    self.history.pop()
        else:
            # Giữ độ dài cố định (cắt đuôi)
            while len(self.history) > self.max_length:
                self.history.pop()

    def check_wall_collision(self) -> bool:
        """Kiểm tra va chạm với tường biên."""
        r = GameConfig.SNAKE_RADIUS
        return (self.x <= r or self.x >= GameConfig.WORLD_WIDTH - r or
                self.y <= r or self.y >= GameConfig.WORLD_HEIGHT - r)

    def get_snapshot(self, max_segments: int = 80) -> dict:
        """
        Tạo snapshot trạng thái để gửi qua mạng.
        Chỉ lấy max_segments đốt đầu để tiết kiệm bandwidth.
        """
        segments = self.history[:max_segments]
        return {
            "player_id": self.player_id,
            "username": self.username,
            "display_name": self.display_name,
            "skin_color": self.skin_color,
            "x": round(self.x, 1),
            "y": round(self.y, 1),
            "angle": round(self.angle, 3),
            "segments": [(round(x, 1), round(y, 1)) for x, y in segments],
            "length": self.length,
            "score": self.score,
            "kills": self.kills,
            "alive": self.alive,
            "is_boosting": self.is_boosting,
        }

    def grow(self, amount: int):
        """Tăng chiều dài rắn."""
        self.max_length += amount
        self.score += amount
        if self.max_length > self.max_length:
            self.max_length = self.max_length

    def generate_death_food(self) -> list:
        """Sinh mồi từ xác rắn khi chết."""
        death_foods = []
        # Cứ 3 đốt tạo 1 hạt mồi lớn
        step = max(3, len(self.history) // 30)
        for i in range(0, len(self.history), step):
            x, y = self.history[i]
            # Thêm offset nhỏ ngẫu nhiên
            x += random.uniform(-15, 15)
            y += random.uniform(-15, 15)
            food = Food(
                x=max(50, min(GameConfig.WORLD_WIDTH - 50, x)),
                y=max(50, min(GameConfig.WORLD_HEIGHT - 50, y)),
                score=GameConfig.DEATH_FOOD_SCORE,
                radius=GameConfig.DEATH_FOOD_RADIUS,
                color=self.skin_color,
                food_type="death"
            )
            death_foods.append(food)
        return death_foods


class GameRoom:
    """
    Quản lý trạng thái 1 phòng game.
    Bao gồm: danh sách rắn, danh sách mồi, logic va chạm, tick loop.
    """

    def __init__(self, room_id: str, room_name: str, host_username: str, max_players: int = 10):
        self.room_id = room_id
        self.room_name = room_name
        self.host_username = host_username
        self.max_players = max_players
        self.status = "WAITING"  # WAITING | PLAYING | CLOSED

        # Dữ liệu game
        self.snakes: dict[str, Snake] = {}    # player_id -> Snake
        self.foods: dict[int, Food] = {}       # food_id -> Food

        # Thống kê phòng
        self.tick_count = 0
        self.game_start_time = None

        # Spawn mồi ban đầu
        self._spawn_initial_food()

    def _spawn_initial_food(self):
        """Tạo mồi ban đầu trên toàn bản đồ."""
        for _ in range(GameConfig.FOOD_COUNT_BASE):
            self._spawn_food()

    def _spawn_food(self):
        """Sinh 1 hạt mồi tại vị trí ngẫu nhiên."""
        margin = 100
        x = random.uniform(margin, GameConfig.WORLD_WIDTH - margin)
        y = random.uniform(margin, GameConfig.WORLD_HEIGHT - margin)
        food = Food(x=x, y=y)
        self.foods[food.id] = food

    def add_player(self, player_id: str, username: str, display_name: str,
                   skin_color: str) -> Snake:
        """Thêm người chơi vào phòng."""
        snake = Snake(player_id, username, display_name, skin_color)
        self.snakes[player_id] = snake
        return snake

    def remove_player(self, player_id: str):
        """Xóa người chơi khỏi phòng."""
        snake = self.snakes.pop(player_id, None)
        if snake and snake.alive:
            # Sinh mồi từ xác
            death_foods = snake.generate_death_food()
            for food in death_foods:
                self.foods[food.id] = food

    def process_input(self, player_id: str, angle: float, is_boosting: bool):
        """Xử lý input từ client."""
        snake = self.snakes.get(player_id)
        if snake and snake.alive:
            snake.target_angle = angle
            snake.is_boosting = is_boosting

    def tick(self) -> list:
        """
        Thực hiện 1 tick game.
        Trả về danh sách sự kiện (player chết, ăn mồi, ...).
        """
        self.tick_count += 1
        events = []

        # Cập nhật vị trí tất cả rắn
        for snake in list(self.snakes.values()):
            if not snake.alive:
                continue
            snake.update()

        # Kiểm tra va chạm
        alive_snakes = [s for s in self.snakes.values() if s.alive]

        for snake in alive_snakes:
            # Va chạm tường
            if snake.check_wall_collision():
                self._kill_snake(snake, killer_id=None, events=events)
                continue

            # Va chạm thân rắn khác (chuẩn cơ chế Slither.io: không tự chết khi chạm vào thân mình)
            for other in alive_snakes:
                if other.player_id == snake.player_id:
                    continue  # Bỏ qua thân của chính mình

                for seg_x, seg_y in other.history:
                    dist = math.hypot(snake.x - seg_x, snake.y - seg_y)
                    if dist < GameConfig.SNAKE_RADIUS + GameConfig.SNAKE_RADIUS * 0.7:
                        killer_id = other.player_id
                        self._kill_snake(snake, killer_id=killer_id, events=events)
                        if killer_id in self.snakes:
                            self.snakes[killer_id].kills += 1
                        break
                else:
                    continue
                break

        # Kiểm tra ăn mồi
        for snake in alive_snakes:
            if not snake.alive:
                continue
            eaten_food_ids = []
            for food in self.foods.values():
                dist = math.hypot(snake.x - food.x, snake.y - food.y)
                if dist < GameConfig.SNAKE_RADIUS + food.radius:
                    eaten_food_ids.append(food.id)
                    snake.grow(food.score)

            for food_id in eaten_food_ids:
                self.foods.pop(food_id, None)
                events.append({
                    "type": "FOOD_EATEN",
                    "player_id": snake.player_id,
                    "food_id": food_id
                })

        # Sinh thêm mồi nếu thiếu
        while len(self.foods) < GameConfig.FOOD_COUNT_BASE:
            for _ in range(GameConfig.FOOD_SPAWN_RATE):
                self._spawn_food()

        return events

    def _kill_snake(self, snake: Snake, killer_id: str | None, events: list):
        """Xử lý rắn chết."""
        if not snake.alive:
            return
        snake.alive = False

        # Sinh mồi từ xác
        death_foods = snake.generate_death_food()
        for food in death_foods:
            self.foods[food.id] = food

        time_alive = int(time.time() - snake.start_time)
        events.append({
            "type": "PLAYER_DEAD",
            "player_id": snake.player_id,
            "username": snake.username,
            "killer_id": killer_id,
            "score": snake.score,
            "max_length": snake.max_length,
            "kills": snake.kills,
            "time_alive": time_alive,
        })

    def get_world_state(self, viewer_id: str = None) -> dict:
        """
        Tạo gói tin WORLD_STATE để gửi cho client.
        Nếu viewer_id được cung cấp, ưu tiên gửi dữ liệu chi tiết hơn cho rắn đó.
        """
        snakes_data = {}
        for pid, snake in self.snakes.items():
            if snake.alive:
                max_seg = 120 if pid == viewer_id else 60
                snakes_data[pid] = snake.get_snapshot(max_segments=max_seg)

        # Chỉ gửi food gần viewer để tiết kiệm bandwidth
        if viewer_id and viewer_id in self.snakes:
            v = self.snakes[viewer_id]
            view_range = 1000
            foods_data = [
                f.to_dict() for f in self.foods.values()
                if abs(f.x - v.x) < view_range and abs(f.y - v.y) < view_range
            ]
        else:
            foods_data = [f.to_dict() for f in list(self.foods.values())[:500]]

        # Bảng xếp hạng trong phòng
        leaderboard = sorted(
            [{"player_id": s.player_id, "display_name": s.display_name,
              "score": s.score, "length": s.length}
             for s in self.snakes.values() if s.alive],
            key=lambda x: x["score"],
            reverse=True
        )[:10]

        return {
            "tick": self.tick_count,
            "snakes": snakes_data,
            "foods": foods_data,
            "leaderboard": leaderboard,
        }

    def get_room_info(self) -> dict:
        """Thông tin phòng để hiển thị trong lobby."""
        return {
            "room_id": self.room_id,
            "room_name": self.room_name,
            "host": self.host_username,
            "status": self.status,
            "players": len(self.snakes),
            "max_players": self.max_players,
        }

    def get_player_list(self) -> list:
        """Danh sách người chơi trong phòng."""
        return [
            {
                "player_id": pid,
                "username": s.username,
                "display_name": s.display_name,
                "skin_color": s.skin_color,
                "is_host": s.username == self.host_username
            }
            for pid, s in self.snakes.items()
        ]
