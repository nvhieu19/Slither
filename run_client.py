#!/usr/bin/env python3
# =============================================================================
# run_client.py - Khởi chạy Game Client
# Môn: Lập Trình Mạng | Game Rắn Săn Mồi Multiplayer
#
# Cách dùng:
#   python run_client.py                              # Kết nối localhost
#   python run_client.py --host 192.168.1.100         # Kết nối server LAN
#   python run_client.py --host 192.168.1.100 --port 12345
# =============================================================================

import sys
import os

# Thêm thư mục gốc vào Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client.client import main

if __name__ == "__main__":
    main()
