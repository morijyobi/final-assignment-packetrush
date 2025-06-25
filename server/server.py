#サーバーの起動、クライアントからの接続を受け付ける、各クライアントのプレイヤー座標を受信、全プレイヤーの情報を全クライアントに送る
import socket
import threading
import json

# サーバーのIPとポート設定
HOST = '0.0.0.0'   # すべてのIPからの接続を受け付ける
PORT = 12345       # 任意のUDPポート

clients = []
positions = {}
# UDPソケット作成
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ソケットをバインド
server_socket.bind((HOST, PORT))
print(f"🟢 サーバー起動: {HOST}:{PORT} で待機中...")

# クライアントからのデータを受信して表示
def handle_client(conn, addr):
    player_id = addr[len(clients)]
    positions[player_id] = {"x": 0, "y": 0} #後で鬼ごっこ開始時の初期座標に更新しないといけない。
    try:
        while True:
            data, addr = server_socket.recvfrom(1024)  # 最大1024バイトまで受信
            reply = "受け取りました"
            server_socket.sendto(reply.encode(), addr)
            conn, addr = server_socket.accept()
            clients.append(conn)
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
            if not data:
                break
            pos = json.loads(data.decode())
            positions[player_id] = pos
            broadcast(json.dumps(positions).encode())
    except Exception as e:
        print(f"エラー:{e}")
    finally:
        conn.close()
        clients.remove(conn)
        del positions[player_id]
def broadcast(message):
    for client in clients:
        try:
            client.sendall(message)
        except:
            pass 