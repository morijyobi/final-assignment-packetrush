#サーバーの起動、クライアントからの接続を受け付ける、各クライアントのプレイヤー座標を受信、全プレイヤーの情報を全クライアントに送る
import socket
import threading
import json

# サーバーのIPとポート設定
HOST = '0.0.0.0'   # すべてのIPからの接続を受け付ける
PORT = 12345       # 任意のUDPポート

# UDPソケット作成
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ソケットをバインド
server_socket.bind((HOST, PORT))
print(f"🟢 サーバー起動: {HOST}:{PORT} で待機中...")

# クライアントからのデータを受信して表示
while True:
    data, addr = server_socket.recvfrom(1024)  # 最大1024バイトまで受信
    print(f"[受信] {addr} から: {data.decode()}")

    # 確認用の応答を返す（任意）
    reply = "受け取りました"
    server_socket.sendto(reply.encode(), addr)