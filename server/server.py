# server/server.py
import socket
import json
import uuid  # プレイヤーIDを一意に発行するため

from server.utils import config as server_config

# UDPソケット作成
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((server_config.HOST, server_config.PORT))
print(f"🟢 サーバー起動: {server_config.HOST}:{server_config.PORT} で待機中...")

# プレイヤー情報を記録する辞書 {addr: {...}}
players = {}

# 必要なプレイヤー数（これで開始）
REQUIRED_PLAYERS = 1

# ゲーム開始フラグ（繰り返し送信を防ぐ）
game_started = False

while True:
    try:
        data, addr = server_socket.recvfrom(1024)
        message = json.loads(data.decode())

        if message.get("type") == "connect_request":
            if addr in players:
                continue  # すでに登録済みなら無視

            player_name = message.get("name", "Unknown")
            player_id = str(uuid.uuid4())[:8]  # 短い一意ID

            players[addr] = {
                "id": player_id,
                "name": player_name,
                "pos": (0, 0),
            }

            print(f"[接続] {addr} が接続。ID: {player_id}, 名前: {player_name}")

            reply = {
                "type": "connect_ack",
                "player_id": player_id
            }
            server_socket.sendto(json.dumps(reply).encode(), addr)

            # ★ プレイヤー人数が揃ったらゲーム開始シグナルを送る
            if len(players) >= REQUIRED_PLAYERS and not game_started:
                print("✅ プレイヤーが揃いました。ゲームを開始します。")
                start_msg = json.dumps({"type": "start_game"}).encode()
                for p_addr in players:
                    server_socket.sendto(start_msg, p_addr)
                game_started = True  # ゲーム開始フラグON
        else:
            print(f"[受信] {addr} から: {message}")

    except Exception as e:
        print(f"[エラー] {e}")