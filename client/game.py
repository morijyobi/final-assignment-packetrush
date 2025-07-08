# game.py
#ソケットの通信の準備、プレイヤー情報の送受信など
import pygame as pg, sys
import socket
import json
import threading
from player import Player
from utils import config
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from server.game_state import GameState

pg.init()
screen = pg.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
WHITE = (255, 255, 255)
# 背景画像
haikeimg = pg.image.load("client/assets/images/map.png")
haikeimg = pg.transform.scale(haikeimg, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
# 制限時間
total_time = 90
class Game:
    def __init__(self, role = "runner"):
        pg.font.init()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(5)
        self.font = pg.font.Font(None, 74)
        self.start_game_time = 0
        self.role = role

        self.server_ip = ""#後でタイトルかロビー画面で入力できるようにする
        self.server_port = config.SERVER_PORT
        self.server_addr = None
        self.player_id = None
        self.ip_entered = False

        self.font = pg.font.SysFont(None, 48)
        self.state = "lobby"  # 追加: ロビー → ゲームの状態を管理
        # クライアントの画面に表示する全プレイヤーのオブジェクトを管理する辞書
        self.all_players_on_screen = {}

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

    # IPアドレス入力画面の描画
    def draw_ip_input(self):
        screen.fill((30, 30, 30))
        title = self.font.render("接続先IPアドレスを入力 (Enterで確定)", True, (255, 255, 255))
        input_text = self.font.render(self.server_ip, True, (0, 255, 0))
        screen.blit(title, (100, 200))
        screen.blit(input_text, (100, 300))
        pg.display.flip()

    # ゲーム開始待機ロビー画面
    def draw_lobby(self):
        screen.fill((20, 20, 60))
        font = pg.font.SysFont(None, 40)
        text = font.render("ロビー：ゲーム開始を待っています...", True, (255, 255, 255))
        screen.blit(text, (100, 250))
        pg.display.flip()

    # ロビーでのIP入力ループ
    def lobby_loop(self):
        while not self.ip_entered:
            self.draw_ip_input()

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
                self.state = "lobby"  # ← これがないとdraw_lobbyが呼ばれない
            else:
                print("[警告] サーバーから未知の応答:", response)
                
        except socket.timeout:
            print("[接続失敗] サーバーから応答なし")

    # サーバーからのメッセージ受信ループ
    def receive_loop(self):
        while True:
            try:
                data, _ = self.socket.recvfrom(2048)
                message = json.loads(data.decode())
                if message.get("type") == "start_game":
                    print("[🎮] ゲーム開始シグナル受信")
                    self.state = "playing"
                    self.start_game_time = pg.time.get_ticks()
                elif message.get("type") == "game_result":
                    print("[🏁] 結果受信: ", message.get("winner"))
                    self.show_result(message.get("winner"))
            except Exception as e:
                print("[受信エラー]", e)
                
    def show_result(self, winner):
        screen.fill((20, 60, 20))
        result_text = self.font.render(f"{winner} の勝ち！", True, (255, 255, 255))
        screen.blit(result_text, (100, 250))
        pg.display.flip()
        pg.time.delay(5000)
        pg.quit()
        sys.exit()

    # ゲーム画面の描画
    def draw(self):
        screen.blit(haikeimg, (0, 0))
        for obs in self.obstacles:
            img = self.obstacle_images.get(obs["type"])
            if img:
                screen.blit(img, obs["pos"])
        pg.display.flip()


    def draw_title(self):
        # タイトル画面(仮)
        self.state = "title"  # タイトル状態に設定
        screen.fill((60, 20, 20))
        font = pg.font.SysFont(None, 40)
        text = font.render("ONI LINK", True, (255,255,255))
        screen.blit(text,(100,250))
        pg.display.flip()
    
    def draw_result(self):
        self.state = "result"  # 結果状態に設定
        screen.fill((20,60,20))
        font = pg.font.SysFont(None,40)
        text = font.render("OOteam Victory!", True,(255,255,255))
        screen.blit(text,(100,250))
        pg.display.flip()

    def run(self):
        self.lobby_loop()

        clock = pg.time.Clock()
        while True:
            if self.state == "lobby":
                self.draw_lobby()
            else:
                self.draw()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
            
            current_time = pg.time.get_ticks()
            elapsed_time = (current_time - self.start_game_time) / 1000
            remaining_time = total_time - elapsed_time
            display_time = int(remaining_time)
            timer_text = self.font.render(f"Time: {display_time}", True, WHITE)
            
            my_player = self.all_players_on_screen.get(self.player_id)
            # キー入力チェック(キー押しっぱなし検出)
            keys = pg.key.get_pressed()

            # メイン処理
            my_player = self.all_players_on_screen.get(self.player_id)
            if my_player and my_player.role == "oni":  # 鬼の移動
                if keys[pg.K_w]: Player.onirect.y += Player.oni_speed
                if keys[pg.K_s]: Player.onirect.y -= Player.oni_speed
                if keys[pg.K_a]: Player.onirect.x -= Player.oni_speed
                if keys[pg.K_d]: Player.onirect.x += Player.oni_speed
            elif my_player:  # 逃げる人の移動
                if keys[pg.K_w]: Player.chararect1.y += Player.player_speed
                if keys[pg.K_s]: Player.chararect1.y -= Player.player_speed
                if keys[pg.K_a]: Player.chararect1.x -= Player.player_speed
                if keys[pg.K_d]: Player.chararect1.x += Player.player_speed

            # 鬼と逃げる人の衝突
            if Player.onirect.colliderect(Player.chararect1):
                Player.chararect1.width = 0
                Player.chararect1.height = 0
            # 鬼の勝ちとして結果を表示        
                self.show_result("鬼")
            # 時間切れ
            if remaining_time <= 0:
                remaining_time = 0
            # 逃げる人の勝ちとして結果を表示
                self.show_result("逃げる人")

            # 捕まった後の確認（既に勝敗処理が終わってなかった場合の保険）
            elif Player.chararect1.width == 0 and Player.chararect1.height == 0:
                self.show_result("鬼")

            
            text_rect = timer_text.get_rect(center=(800 // 2, 50))
            screen.blit(timer_text, text_rect)
            
            pg.display.flip() # 画面更新
            clock.tick(60) # FPS 60 に制限
            
if __name__ == "__main__":
    game = Game()
    game.run()
