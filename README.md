# 🐍 Slither.io — Multiplayer Snake Battle

> **Môn:** Lập Trình Mạng | **Ngôn ngữ:** Python 3.11+ | **Framework:** Pygame-CE + TCP Socket  
> **Kiến trúc:** Client-Server với giao thức TCP tùy chỉnh + MySQL

---

## 🎮 Giới thiệu dự án

**Slither.io** là game rắn săn mồi nhiều người chơi theo thời gian thực, lấy cảm hứng từ trò chơi nổi tiếng slither.io. Người chơi điều khiển một con rắn trên bản đồ rộng lớn, thu thập thức ăn để lớn dần và tiêu diệt các rắn đối thủ bằng cách khiến họ đâm vào thân mình.

### ✨ Tính năng nổi bật
- 🌐 **Multiplayer realtime** qua TCP Socket — nhiều người chơi đồng thời
- 🎨 **Đồ họa đẹp** với hiệu ứng Glow, Gradient, Particles
- 🔑 **Hệ thống tài khoản** — Đăng ký / Đăng nhập / Tùy chỉnh Skin
- 🏠 **Hệ thống phòng** — Tạo phòng, mời bạn bè, chat trong phòng chờ
- 💬 **Chat realtime** trong phòng chờ và trong game
- 📊 **Bảng xếp hạng** realtime trong trận và bảng tổng MySQL
- 🗄️ **MySQL Database** — Lưu lịch sử, kỷ lục, tài khoản
- 🗺️ **Radar Minimap** — Hiển thị vị trí tất cả rắn thu nhỏ

---

## 🗂️ Cấu trúc thư mục

```
Slither/
├── run_server.py          # 🟢 Khởi chạy Server
├── run_client.py          # 🔵 Khởi chạy Client
├── requirements.txt       # Danh sách thư viện
│
├── shared/                # Module dùng chung Client & Server
│   ├── __init__.py
│   └── protocol.py        # Định nghĩa giao thức mạng + hằng số game
│
├── server/                # 🖥️ Phía Server
│   ├── __init__.py
│   ├── server.py          # Server TCP đa luồng, xử lý clients
│   └── game_logic.py      # Logic game: Snake, Food, GameRoom, Physics
│
├── client/                # 💻 Phía Client
│   ├── __init__.py
│   ├── client.py          # Game client chính, vòng lặp Pygame
│   ├── network.py         # Quản lý kết nối TCP + recv thread
│   ├── renderer.py        # Module vẽ đồ họa Pygame
│   └── ui_screens.py      # Các màn hình: Menu, Login, Lobby, Room, BXH
│
├── database/              # 🗄️ Cơ sở dữ liệu
│   ├── __init__.py
│   ├── db_manager.py      # Quản lý MySQL (Connection Pool)
│   └── schema.sql         # Script tạo bảng MySQL
│
└── assets/                # Tài nguyên (font, ảnh, âm thanh)
    ├── fonts/
    ├── images/
    └── sounds/
```

---

## ⚙️ Cài đặt & Chạy

### Yêu cầu hệ thống
- Python **3.11+**
- (Tùy chọn) MySQL Server 8.0+ — Nếu không có MySQL, game vẫn chạy được với dữ liệu trong RAM

### Bước 1: Cài đặt thư viện

```bash
cd Slither
pip install -r requirements.txt
```

### Bước 2: Cài đặt MySQL (Tùy chọn)

```bash
# Chạy script SQL trong MySQL Workbench hoặc terminal:
mysql -u root -p < database/schema.sql
```

> **Lưu ý:** Nếu không có MySQL, game vẫn hoạt động hoàn toàn với chế độ **Mock DB** (lưu trong RAM). Tài khoản demo: `demo/demo123`, `player1/demo123`

### Bước 3: Chạy Server

```bash
# Cửa sổ Terminal 1 — Khởi động Server
python run_server.py

# Hoặc tùy chỉnh host/port:
python run_server.py --host 0.0.0.0 --port 12345
```

### Bước 4: Chạy Client (Mỗi người chơi 1 cửa sổ)

```bash
# Cửa sổ Terminal 2, 3, ... — Khởi động Client
python run_client.py

# Kết nối tới server LAN:
python run_client.py --host 192.168.1.100
```

---

## 🕹️ Hướng dẫn chơi

| Hành động | Phím / Chuột |
|-----------|-------------|
| Điều hướng rắn | Di chuyển chuột |
| Bứt tốc (giảm thân) | Giữ **Chuột trái** hoặc **Space** |
| Hồi sinh sau khi chết | **Space** |
| Quay lại / Thoát phòng | **ESC** |

### Luật chơi
- 🐍 Thu thập hạt mồi để tăng điểm và chiều dài thân
- 💥 Nếu đầu rắn đâm vào thân rắn khác hoặc tường → chết
- 💀 Khi rắn chết → toàn bộ thân biến thành mồi năng lượng cao cho người khác
- ⚡ Bứt tốc tiêu tốn chiều dài thân rắn

---

## 🌐 Giao thức mạng

Game sử dụng **TCP Socket** với giao thức tùy chỉnh:

```
[4 bytes Header: độ dài JSON] + [JSON payload]
```

| Loại gói tin | Chiều | Mô tả |
|-------------|-------|-------|
| `LOGIN_REQ / RES` | C→S / S→C | Xác thực tài khoản |
| `REGISTER_REQ / RES` | C→S / S→C | Đăng ký tài khoản |
| `CREATE_ROOM_REQ / RES` | C→S / S→C | Tạo phòng |
| `JOIN_ROOM_REQ / RES` | C→S / S→C | Vào phòng |
| `START_GAME_REQ` | C→S | Bắt đầu game (Host) |
| `PLAYER_INPUT` | C→S | Góc quay + trạng thái Boost (~60/giây) |
| `WORLD_STATE` | S→C | Trạng thái thế giới (30/giây) |
| `PLAYER_DEAD` | S→C | Thông báo rắn chết |
| `CHAT_MSG / BROADCAST` | C↔S | Tin nhắn chat |

---

## 👥 Phân công thành viên

*(Chi tiết xem file `README_PHAN_CONG.md`)*

| Thành viên | Vai trò | Module chính |
|-----------|---------|-------------|
| Thành viên 1 | Client Lead | `client.py`, `renderer.py` |
| Thành viên 2 | UI Designer | `ui_screens.py`, đồ họa |
| Thành viên 3 | Network Engineer | `network.py`, `protocol.py` |
| Thành viên 4 | Server Developer | `server.py`, `game_logic.py` |
| Thành viên 5 | Database & Docs | `db_manager.py`, báo cáo |

---

## 🗄️ Database Schema

```sql
users          -- Tài khoản: username, password_hash (SHA-256), skin_color, highest_score
match_history  -- Lịch sử ván đấu: score, max_length, kills, time_alive
rooms          -- Phòng chơi: room_id, room_name, host, status
```

---

## 📦 Công nghệ sử dụng

| Công nghệ | Phiên bản | Mục đích |
|-----------|-----------|---------|
| Python | 3.11+ | Ngôn ngữ chính |
| Pygame-CE | 2.5+ | Đồ họa game Client |
| socket (stdlib) | - | Giao tiếp mạng TCP |
| threading (stdlib) | - | Đa luồng Server |
| mysql-connector-python | 8.3+ | Kết nối MySQL |
| json (stdlib) | - | Định dạng gói tin |
| struct (stdlib) | - | Đóng gói binary header |
