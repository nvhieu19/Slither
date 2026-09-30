#!/usr/bin/env python3
# =============================================================================
# run_server.py - Khởi chạy Game Server
# Môn: Lập Trình Mạng | Game Rắn Săn Mồi Multiplayer
#
# Cách dùng:
#   python run_server.py                    # Mặc định 127.0.0.1:12345
#   python run_server.py --host 0.0.0.0     # Cho phép kết nối từ ngoài
#   python run_server.py --port 8888        # Dùng port khác
# =============================================================================

import sys
import os

# Thêm thư mục gốc vào Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.server import GameServer
from shared.protocol import GameConfig

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="🐍 Slither.io Game Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python run_server.py
  python run_server.py --host 0.0.0.0 --port 12345
  python run_server.py --host 192.168.1.100
        """
    )
    parser.add_argument("--host", default=GameConfig.SERVER_HOST,
                        help=f"Địa chỉ IP lắng nghe (mặc định: {GameConfig.SERVER_HOST})")
    parser.add_argument("--port", type=int, default=GameConfig.SERVER_PORT,
                        help=f"Cổng lắng nghe (mặc định: {GameConfig.SERVER_PORT})")
    args = parser.parse_args()

    print("=" * 60)
    print("  🐍 SLITHER.IO - MULTIPLAYER SNAKE BATTLE SERVER")
    print("  Môn: Lập Trình Mạng | Python TCP Socket")
    print("=" * 60)
    print(f"  Host  : {args.host}")
    print(f"  Port  : {args.port}")
    print(f"  Tickrate: {GameConfig.SERVER_TICKRATE} FPS")
    print("=" * 60)
    print("  Nhấn Ctrl+C để dừng server")
    print()

    server = GameServer(host=args.host, port=args.port)
    server.start()
