# server/server.py
import socket
import json
import uuid  # プレイヤーIDを一意に発行するため

# サーバーの設定を外部から読み込む
from server.utils import config as server_config

positions = {}
data_list = [] #受信したデータを記憶するリスト
# UDPソケット作成
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((server_config.HOST, server_config.PORT))
print(f"🟢 サーバー起動: {server_config.HOST}:{server_config.PORT} で待機中...")

# プレイヤー情報を記録する辞書 {addr: {"id": ..., "name": ..., "pos": (x, y)}}
players = {}
while True:
    try:
        data, addr = server_socket.recvfrom(1024)
        message = json.loads(data.decode())
        decode_data = data.decode("utf-8")
        print(f"[受信] {addr} から: {decode_data}")
        data_list.append(decode_data)
        # 接続要求の処理
        if message.get("type") == "connect_request":
            player_name = message.get("name", "Unknown")
            player_id = str(uuid.uuid4())[:8]  # 短い一意IDを発行

            players[addr] = {
                "id": player_id,
                "name": player_name,
                "pos": (0, 0),  # 仮の初期位置
            }

            print(f"[接続] {addr} が接続。ID: {player_id}, 名前: {player_name}")
            print(data_list)#受信したデータを記憶するリストのテスト
            reply = {
                "type": "connect_ack",
                "player_id": player_id
            }
            server_socket.sendto(json.dumps(reply).encode(), addr)
        else:
            print(f"[受信] {addr} から: {message}")
            # ここに他のメッセージタイプの処理を今後追加

    except Exception as e:
        print("[ERROR]", e)