# 📋 BẢNG PHÂN CÔNG NHIỆM VỤ — NHÓM DỰ ÁN

## 🐍 Dự án: Slither.io — Game Rắn Săn Mồi Multiplayer

**Môn:** Lập Trình Mạng | **Công nghệ:** Python 3.11 + Pygame-CE + TCP Socket + MySQL

---

## 👥 Danh sách thành viên nhóm

| STT | Họ và tên       | MSSV | Vai trò                            | Email |
| --- | ------------------ | ---- | ----------------------------------- | ----- |
| 1   | Nguyễn Văn Hiếu | 0    | **Client Lead / Game Engine** |       |
| 2   | Trần Minh Hải    | 0    | **UI/UX Designer**            |       |
| 3   | Phạm Quang        | 0    | **Network Engineer**          |       |
| 4   | Nguyễn Văn Long  | 0    | **Server Developer**          |       |
| 5   | Lê Thịnh         | 0    | **Database & Documentation**  |       |

---

## 📌 PHÂN CÔNG CHI TIẾT

### 🟢 Nguyễn Văn Hiếu — Client Lead / Game Engine

> **File chính:** `client/client.py`, `client/renderer.py`

| #   | Nhiệm vụ                         | Chi tiết                                              | Trạng thái    |
| --- | ---------------------------------- | ------------------------------------------------------ | --------------- |
| 1.1 | Vòng lặp game chính (Game Loop) | Thiết kế state machine, FPS control, delta time      | ✅ Hoàn thành |
| 1.2 | Camera system                      | Smooth camera follow với lerp interpolation           | ✅ Hoàn thành |
| 1.3 | Render rắn (Snake Renderer)       | Vẽ thân gradient, đầu rắn, mắt liếc theo chuột | ✅ Hoàn thành |
| 1.4 | Hiệu ứng Glow                    | Additive blending cho đầu rắn và mồi phát sáng  | ✅ Hoàn thành |
| 1.5 | Particle system                    | Mảnh vỡ khi ăn mồi, vệt boost                     | ✅ Hoàn thành |
| 1.6 | Điều khiển chuột               | Tính toán góc`math.atan2`, gửi input 60/giây    | ✅ Hoàn thành |
| 1.7 | Render background                  | Lưới nền động, viền bản đồ nhấp nháy        | ✅ Hoàn thành |
| 1.8 | Tích hợp network với game loop  | Đọc WORLD_STATE, apply lên renderer                 | ✅ Hoàn thành |

**Công nghệ:** `pygame-ce`, `math`, `threading`

---

### 🔵 Trần Minh Hải — UI/UX Designer

> **File chính:** `client/ui_screens.py`

| #   | Nhiệm vụ                     | Chi tiết                                        | Trạng thái    |
| --- | ------------------------------ | ------------------------------------------------ | --------------- |
| 2.1 | Màn hình Main Menu           | Rắn animated nền, buttons gradient, logo pulse | ✅ Hoàn thành |
| 2.2 | Form Đăng nhập / Đăng ký | InputBox có placeholder/password, validation UX | ✅ Hoàn thành |
| 2.3 | Màn hình Lobby               | Room list scrollable, tabs "Phòng" / "Skin"     | ✅ Hoàn thành |
| 2.4 | Skin Customizer                | Grid 36 màu, preview rắn animated, lưu DB     | ✅ Hoàn thành |
| 2.5 | Màn hình Room Waiting        | Danh sách player, chat, nút Start host         | ✅ Hoàn thành |
| 2.6 | HUD In-game                    | Score bar, leaderboard panel, chat overlay       | ✅ Hoàn thành |
| 2.7 | Radar Minimap                  | Scale tọa độ World→Minimap, chấm xanh/đỏ  | ✅ Hoàn thành |
| 2.8 | Màn hình Game Over           | Thống kê ván đấu, hướng dẫn hồi sinh    | ✅ Hoàn thành |
| 2.9 | Bảng xếp hạng tổng         | Top 20 với medal, animation nền                | ✅ Hoàn thành |

**Công nghệ:** `pygame-ce`, `math`, CSS-like styling trong Pygame

---

### 🟡 Phạm Quang — Network Engineer

> **File chính:** `client/network.py`, `shared/protocol.py`

| #   | Nhiệm vụ                | Chi tiết                                             | Trạng thái    |
| --- | ------------------------- | ----------------------------------------------------- | --------------- |
| 3.1 | Thiết kế giao thức TCP | Header 4-byte length + JSON payload                   | ✅ Hoàn thành |
| 3.2 | PacketReader              | Đọc đúng n bytes, xử lý sticky packets          | ✅ Hoàn thành |
| 3.3 | Encode/Decode packet      | `struct.pack/unpack`, `json`, UTF-8               | ✅ Hoàn thành |
| 3.4 | NetworkClient class       | Kết nối TCP, timeout, retry logic                   | ✅ Hoàn thành |
| 3.5 | Recv Thread               | Thread riêng nhận dữ liệu, không block game loop | ✅ Hoàn thành |
| 3.6 | Thread-safe Queue         | `queue.Queue` truyền packets sang game thread      | ✅ Hoàn thành |
| 3.7 | Xử lý ngắt kết nối   | Detect CONNECTION_LOST, notify UI                     | ✅ Hoàn thành |
| 3.8 | Giao thức Input          | Gửi`PLAYER_INPUT` 60 lần/giây (angle + boost)    | ✅ Hoàn thành |
| 3.9 | Tất cả hàm send        | login, register, room CRUD, chat, respawn             | ✅ Hoàn thành |

**Công nghệ:** `socket`, `threading`, `queue`, `json`, `struct`

---

### 🔴 Nguyễn Văn Long — Server Developer

> **File chính:** `server/server.py`, `server/game_logic.py`

| #    | Nhiệm vụ            | Chi tiết                                          | Trạng thái    |
| ---- | --------------------- | -------------------------------------------------- | --------------- |
| 4.1  | TCP Server đa luồng | Accept loop, ClientHandler Thread mỗi client      | ✅ Hoàn thành |
| 4.2  | Routing packet        | Handler dict điều phối theo packet type         | ✅ Hoàn thành |
| 4.3  | Snake class           | History segments, update position, angle lerp      | ✅ Hoàn thành |
| 4.4  | Food class            | Spawn ngẫu nhiên, pulse animation data           | ✅ Hoàn thành |
| 4.5  | GameRoom class        | Quản lý phòng, tick loop, broadcast             | ✅ Hoàn thành |
| 4.6  | Game Loop per Room    | Thread riêng cho mỗi phòng, tickrate 30 FPS     | ✅ Hoàn thành |
| 4.7  | Collision Detection   | Đầu-thân (khoảng cách), đầu-tường (biên) | ✅ Hoàn thành |
| 4.8  | Death Mechanic        | Sinh food từ History rắn chết                   | ✅ Hoàn thành |
| 4.9  | Boost mechanic        | Tăng tốc, tiêu tốn chiều dài mỗi N frame    | ✅ Hoàn thành |
| 4.10 | World State broadcast | Tổng hợp snakes + foods + BXH gửi mỗi tick     | ✅ Hoàn thành |
| 4.11 | Disconnect handling   | Try-catch, dọn rắn, sinh xác                    | ✅ Hoàn thành |
| 4.12 | Food spawner          | Giữ số lượng mồi tối thiểu trên map        | ✅ Hoàn thành |

**Công nghệ:** `socket`, `threading`, `math`, `time`, `uuid`

---

### 🟣 Lê Thịnh — Database & Documentation

> **File chính:** `database/db_manager.py`, `database/schema.sql`, báo cáo Word

| #    | Nhiệm vụ                   | Chi tiết                                       | Trạng thái    |
| ---- | ---------------------------- | ----------------------------------------------- | --------------- |
| 5.1  | Thiết kế schema MySQL      | 3 bảng: users, match_history, rooms + VIEW BXH | ✅ Hoàn thành |
| 5.2  | Connection Pool              | `mysql.connector.pooling`, pool_size=10       | ✅ Hoàn thành |
| 5.3  | Xác thực tài khoản       | Register/Login với SHA-256, duplicate check    | ✅ Hoàn thành |
| 5.4  | Lưu lịch sử ván đấu    | INSERT match_history khi rắn chết             | ✅ Hoàn thành |
| 5.5  | Cập nhật kỷ lục          | UPDATE highest_score nếu phá kỷ lục         | ✅ Hoàn thành |
| 5.6  | Mock DB mode                 | Fallback khi không có MySQL (RAM storage)     | ✅ Hoàn thành |
| 5.7  | Leaderboard query            | ORDER BY highest_score DESC, LIMIT 20           | ✅ Hoàn thành |
| 5.8  | Update skin                  | UPDATE skin_color trong DB                      | ✅ Hoàn thành |
| 5.9  | Báo cáo Word — Chương 1 | Tổng quan, công nghệ, kiến trúc hệ thống | ✅ Hoàn thành |
| 5.10 | Báo cáo Word — Chương 2 | Phân tích thiết kế, lược đồ, giao thức | ✅ Hoàn thành |
| 5.11 | Báo cáo Word — Chương 3 | Kết quả, demo screenshots, kết luận         | ✅ Hoàn thành |
| 5.12 | README phân công           | File này                                       | ✅ Hoàn thành |

**Công nghệ:** `mysql-connector-python`, SQL, Microsoft Word

---

## 📊 Phân bổ công việc tổng quan

```
Nguyễn Văn Hiếu (Client/Engine):   ██████████ 20% 
Trần Minh Hải (UI/UX):           ████████████ 25%
Phạm Quang (Network):         ████████ 18%
Nguyễn Văn Long (Server):          ████████████ 24%
Lê Thịnh (DB/Docs):         ██████ 13%
```

---

## 🔗 Giao diện giữa các module

```
Client (Thành viên 1, 2, 3)
    │
    │  TCP Socket (Thành viên 3)
    │  Protocol: PacketType, encode/decode
    │
Server (Thành viên 4)
    │
    │  Python API (db_manager)
    │
Database MySQL (Thành viên 5)
```

---

## 📅 Timeline dự kiến

| Tuần   | Công việc                                        |
| ------- | -------------------------------------------------- |
| Tuần 1 | Thiết kế kiến trúc, giao thức, setup project  |
| Tuần 2 | Server core: TCP listen, client handler, game room |
| Tuần 3 | Client core: Pygame window, network recv thread    |
| Tuần 4 | Game logic: Snake, Food, Collision, Physics        |
| Tuần 5 | UI screens: Menu, Auth, Lobby, Room, HUD           |
| Tuần 6 | Database: Schema, CRUD, Connection Pool            |
| Tuần 7 | Tích hợp, test, sửa bug                         |
| Tuần 8 | Hoàn thiện báo cáo, demo                       |

---

## 📝 Ghi chú

- Source code được quản lý tại thư mục `Slither/`
- Tất cả comment trong code viết bằng tiếng Việt để dễ đọc báo cáo
- Chạy được **không cần MySQL** (mock mode tự động bật nếu không kết nối được DB)
- Game test được với 1 người chơi (solo) hoặc nhiều người qua LAN
