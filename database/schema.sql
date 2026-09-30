-- =============================================================================
-- database/schema.sql - Schema MySQL cho Game Rắn Săn Mồi Multiplayer
-- Môn: Lập Trình Mạng | Python TCP Socket
-- =============================================================================

-- Tạo database
CREATE DATABASE IF NOT EXISTS slither_game
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE slither_game;

-- ==============================
-- BẢNG 1: NGƯỜI DÙNG (USERS)
-- ==============================
CREATE TABLE IF NOT EXISTS users (
    id              INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Khóa chính',
    username        VARCHAR(50) UNIQUE NOT NULL COMMENT 'Tên đăng nhập (duy nhất)',
    password_hash   VARCHAR(64) NOT NULL COMMENT 'Hash SHA-256 của mật khẩu',
    display_name    VARCHAR(100) COMMENT 'Tên hiển thị trong game',
    skin_color      VARCHAR(7) DEFAULT '#4ECDC4' COMMENT 'Mã màu HEX skin rắn',
    highest_score   INT DEFAULT 0 COMMENT 'Điểm cao nhất đạt được',
    total_kills     INT DEFAULT 0 COMMENT 'Tổng số rắn tiêu diệt',
    total_games     INT DEFAULT 0 COMMENT 'Tổng số ván đấu đã chơi',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời điểm tạo tài khoản',
    last_login      DATETIME COMMENT 'Lần đăng nhập cuối',
    INDEX idx_highest_score (highest_score DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Bảng tài khoản người chơi';

-- ==============================
-- BẢNG 2: LỊCH SỬ TRẬN ĐẤU
-- ==============================
CREATE TABLE IF NOT EXISTS match_history (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL COMMENT 'FK tới users.id',
    username    VARCHAR(50) COMMENT 'Cache tên user',
    score       INT DEFAULT 0 COMMENT 'Điểm ván đấu này',
    max_length  INT DEFAULT 0 COMMENT 'Chiều dài tối đa đạt được',
    kills       INT DEFAULT 0 COMMENT 'Số rắn tiêu diệt trong ván',
    time_alive  INT DEFAULT 0 COMMENT 'Thời gian sống (giây)',
    played_at   DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời điểm chơi',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_score (score DESC),
    INDEX idx_played_at (played_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Lịch sử kết quả từng ván đấu';

-- ==============================
-- BẢNG 3: PHÒNG CHƠI (ROOMS)
-- ==============================
CREATE TABLE IF NOT EXISTS rooms (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    room_id         VARCHAR(20) UNIQUE NOT NULL COMMENT 'ID phòng (VD: R1A2B3)',
    room_name       VARCHAR(100) COMMENT 'Tên phòng hiển thị',
    host_username   VARCHAR(50) COMMENT 'Tên đăng nhập của chủ phòng',
    status          ENUM('WAITING','PLAYING','CLOSED') DEFAULT 'WAITING',
    max_players     INT DEFAULT 10 COMMENT 'Số người chơi tối đa',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Quản lý phòng chơi (lịch sử)';

-- ==============================
-- DỮ LIỆU MẪU ĐỂ TEST
-- ==============================
-- Mật khẩu đều là "demo123" (SHA-256)
INSERT IGNORE INTO users (username, password_hash, display_name, skin_color, highest_score, total_kills, total_games)
VALUES
    ('demo',    'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'Demo Player', '#FF6B6B', 5000, 25, 10),
    ('player1', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'Player One',  '#4ECDC4', 8000, 40, 20),
    ('player2', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'Player Two',  '#45B7D1', 3000, 15, 8);

-- ==============================
-- VIEW: BXH TỔNG HỢP
-- ==============================
CREATE OR REPLACE VIEW v_leaderboard AS
SELECT
    u.username,
    u.display_name,
    u.skin_color,
    u.highest_score,
    u.total_kills,
    u.total_games,
    IFNULL(AVG(m.score), 0) AS avg_score
FROM users u
LEFT JOIN match_history m ON u.id = m.user_id
GROUP BY u.id
ORDER BY u.highest_score DESC;

SELECT 'Schema đã khởi tạo thành công!' AS message;
