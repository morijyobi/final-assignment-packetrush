#ソケットの通信の準備、プレイヤー情報の送受信など
import pygame as pg, sys
import socket
import json
import threading
from player import Player
from utils import config

pg.init()
screen = pg.display.set_mode((800, 600))

# 背景画像
haikeimg = pg.image.load("client/assets/images/map.png")
haikeimg = pg.transform.scale(haikeimg, (800, 600))

class Game:
    def __init__(self):
        # ソケット通信の初期化
        self.server_addr = (config.SERVER_HOST, config.SERVER_PORT)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(5)

        self.player_id = None
        self.state = "lobby"  # 追加: ロビー → ゲームの状態を管理

        # サーバーに接続要求を送信
        self.send_connect_request()

        # サーバーからのメッセージを待機するスレッド
        threading.Thread(target=self.receive_loop, daemon=True).start()

        # 障害物画像
        self.obstacle_images = {
            "momiji": pg.transform.scale(pg.image.load("client/assets/images/momiji.png"), (60, 60)),
            "ido": pg.transform.scale(pg.image.load("client/assets/images/ido_gray.png"), (30, 30)),
            "iwa": pg.transform.scale(pg.image.load("client/assets/images/iwa_01.png"), (30, 30)),
            "otera": pg.transform.scale(pg.image.load("client/assets/images/otera.png"), (80, 80)),
            "torii": pg.transform.scale(pg.image.load("client/assets/images/torii01.png"), (80, 80))
        }

        # 障害物データ
        self.obstacles = [
            {"type": "momiji", "pos": (230, 180)},
            {"type": "momiji", "pos": (230, 260)},
            {"type": "momiji", "pos": (230, 340)},
            {"type": "otera", "pos": (380, 50)},
            {"type": "torii", "pos": (383, 130)},
            {"type": "iwa", "pos": (350, 250)},
            {"type": "iwa", "pos": (450, 330)},
            {"type": "ido", "pos": (500, 90)},
            {"type": "momiji", "pos": (530, 180)},
            {"type": "momiji", "pos": (530, 260)},
            {"type": "momiji", "pos": (530, 340)}
        ]

    def send_connect_request(self):
        connect_msg = {
            "type": "connect_request",
            "name": "Player1"
        }
        self.socket.sendto(json.dumps(connect_msg).encode(), self.server_addr)
        try:
            data, _ = self.socket.recvfrom(1024)
            response = json.loads(data.decode())
            if response.get("type") == "connect_ack":
                self.player_id = response["player_id"]
                print(f"[接続成功] プレイヤーID: {self.player_id}")
            else:
                print("[警告] サーバーから未知の応答:", response)
        except socket.timeout:
            print("[接続失敗] サーバーから応答なし")

    def receive_loop(self):
        # サーバーからのデータを受信し続けるループ
        while True:
            try:
                data, _ = self.socket.recvfrom(2048)
                message = json.loads(data.decode())
                if message.get("type") == "start_game":
                    print("[🎮] ゲーム開始シグナル受信")
                    self.state = "playing"  # ロビーからプレイ状態へ遷移
            except Exception as e:
                print("[受信エラー]", e)

    def draw(self):
        # ゲームプレイ画面の描画
        screen.blit(haikeimg, (0, 0))
        for obs in self.obstacles:
            img = self.obstacle_images.get(obs["type"])
            if img:
                screen.blit(img, obs["pos"])
        pg.display.flip()

    def draw_lobby(self):
        # ロビー画面の描画（仮）
        screen.fill((20, 20, 60))
        font = pg.font.SysFont(None, 40)
        text = font.render("ロビー：ゲーム開始を待っています...", True, (255, 255, 255))
        screen.blit(text, (100, 250))
        pg.display.flip()

    def run(self):
        clock = pg.time.Clock() # FPS調整用
        while True:
            # イベント処理
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()

            # ゲーム状態に応じた処理
            if self.state == "lobby":
                self.draw_lobby()
            elif self.state == "playing":
                self.draw()
                # キー入力チェック(キー押しっぱなし検出)
                keys = pg.key.get_pressed()
                if keys[pg.K_w]:
                    print("Wキーが押されています")
                if keys[pg.K_s]:
                    print("Sキーが押されています")
                if keys[pg.K_a]:
                    print("Aキーが押されています")
                if keys[pg.K_d]:
                    print("Dキーが押されています")

            clock.tick(60) # FPS 60 に制限

if __name__ == "__main__":
    game = Game()
    game.run()