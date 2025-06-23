#サーバーの起動、クライアントからの接続を受け付ける、各クライアントのプレイヤー座標を受信、全プレイヤーの情報を全クライアントに送る
import socket
import threading
import json

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_addr = ('localhost', 12345)

while True:
    msg = input("送信するメッセージ > ")
    if msg == "exit":
        break
    client_socket.sendto(msg.encode(), server_addr)
    data, _ = client_socket.recvfrom(1024)
    print("[サーバーの応答]:", data.decode())