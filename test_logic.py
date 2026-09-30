import sys
sys.path.insert(0, 'C:/Users/Otis/Desktop/LapTrinhMang/Slither')

# Test import shared
from shared.protocol import PacketType, GameConfig, encode_packet, decode_packet, PacketReader
print('OK shared.protocol')

# Test game logic
from server.game_logic import Food, Snake, GameRoom
print('OK server.game_logic')

# Test encode/decode
pkt = encode_packet('TEST', {'hello': 'world'})
print('OK encode_packet - bytes:', len(pkt))

# Test game room
room = GameRoom('R001', 'Test Room', 'admin')
snake = room.add_player('P1', 'user1', 'User One', '#FF6B6B')
print('OK GameRoom - foods spawned:', len(room.foods))

# Test spawn geometry: các đốt thân phải cách nhau an toàn
d_head_to_seg20 = ((snake.x - snake.history[20][0])**2 + (snake.y - snake.history[20][1])**2)**0.5
assert d_head_to_seg20 > 50, f"Distance head to segment 20 must be > 50px, got {d_head_to_seg20}"
print(f'OK Snake spawn geometry - dist to seg 20: {d_head_to_seg20:.1f}px')

# Test tick: kiểm tra rắn sống sót qua tick đầu và 50 ticks liên tiếp
for tick_i in range(50):
    events = room.tick()
    assert snake.alive, f"Snake died unexpectedly on tick {tick_i+1}!"

# Test quay đầu đâm vào thân mình: rắn không được phép chết vì thân của chính nó
snake.target_angle = snake.angle + 3.14159
for _ in range(20):
    room.tick()
assert snake.alive, "Rắn không được phép tự chết khi chạm vào thân chính mình!"
print('OK Game tick survival - rắn không bị tự chết khi chạm vào thân mình')

# World state
ws = room.get_world_state()
snakes_count = len(ws['snakes'])
foods_count = len(ws['foods'])
print('OK World state - snakes:', snakes_count, 'foods:', foods_count)

# Test death mechanic
snake2 = room.add_player('P2', 'user2', 'User Two', '#4ECDC4')
# Force kill
snake2.alive = False
death_food = snake2.generate_death_food()
print('OK Death mechanic - death food count:', len(death_food))

# Test DB manager (mock mode)
from database.db_manager import DatabaseManager
db = DatabaseManager()  # Will use mock mode since no MySQL
r = db.register_user('testuser', 'testpass123', 'Test User')
print('OK DB register (mock):', r['success'])
r2 = db.login_user('testuser', 'testpass123')
print('OK DB login (mock):', r2['success'])

print()
print('===== ALL TESTS PASSED =====')
