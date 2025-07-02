# ソケットの通信の準備、プレイヤー情報の送受信など
import pygame as pg, sys
import socket
import json
from player import Player
from utils import config

pg.init()
screen = pg.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

# 背景画像
haikeimg = pg.image.load("client/assets/images/map.png")
haikeimg = pg.transform.scale(haikeimg, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

class Game:
    def __init__(self):
        pg.font.init()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(5)

        self.server_ip = ""
        self.server_port = config.SERVER_PORT
        self.server_addr = None
        self.player_id = None
        self.ip_entered = False

        self.font = pg.font.SysFont(None, 48)

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

    # ロビー画面の描画
    def draw_lobby(self):
        screen.fill((30, 30, 30))
        title = self.font.render("接続先IPアドレスを入力 (Enterで確定)", True, (255, 255, 255))
        input_text = self.font.render(self.server_ip, True, (0, 255, 0))
        screen.blit(title, (100, 200))
        screen.blit(input_text, (100, 300))
        pg.display.flip()

    # ロビーでのIP入力ループ
    def lobby_loop(self):
        while not self.ip_entered:
            self.draw_lobby()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_RETURN:
                        self.ip_entered = True
                        self.send_connect_request()
                    elif event.key == pg.K_BACKSPACE:
                        self.server_ip = self.server_ip[:-1]
                    else:
                        if len(self.server_ip) < 15:
                            self.server_ip += event.unicode

    # サーバーへの接続要求を送る
    def send_connect_request(self):
        self.server_addr = (self.server_ip, self.server_port)
        connect_msg = {
            "type": "connect_request",
            "name": "Player"
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

    # ゲーム画面の描画
    def draw(self):
        screen.blit(haikeimg, (0, 0))
        for obs in self.obstacles:
            img = self.obstacle_images.get(obs["type"])
            if img:
                screen.blit(img, obs["pos"])
        pg.display.flip()

    # ゲームループ
    def run(self):
        self.lobby_loop()  # ← まずIPアドレスを入力

        clock = pg.time.Clock()
        while True:
            self.draw()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
            keys = pg.key.get_pressed()
            if keys[pg.K_w]:
                print("Wキーが押されています")
            if keys[pg.K_s]:
                print("Sキーが押されています")
            if keys[pg.K_a]:
                print("Aキーが押されています")
            if keys[pg.K_d]:
                print("Dキーが押されています")
            clock.tick(config.FPS)

# メイン処理
if __name__ == "__main__":
    game = Game()
    game.run()
