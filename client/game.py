# game.py
#ソケットの通信の準備、プレイヤー情報の送受信など
import pygame as pg, sys
import socket
import json
import threading
from client.player import Player
from client.utils import config
import os
import tkinter as tk
from tkinter import messagebox
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from server.game_state import GameState
# デプロイするときにファイルのパスでエラーが出てしまうのでそれを解消する関数
def resource_path(relative_path):
    # PyInstallerが一時展開するフォルダを参照
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
pg.init()
screen = pg.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
WHITE = (255, 255, 255)
# 背景画像
image_path1 = resource_path("client/assets/images/map.png")
haikeimg = pg.image.load(image_path1)
haikeimg = pg.transform.scale(haikeimg, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
lobby_path = resource_path("client/assets/images/lobby.png")
lobbyimg = pg.image.load(lobby_path)
lobbyimg = pg.transform.scale(lobbyimg, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
title_path = resource_path("client/assets/images/onitop.png")
titleimg = pg.image.load(title_path)
titleimg = pg.transform.scale(titleimg, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
# 制限時間
total_time = 90
class Game:
    def __init__(self, role = "runner"):
        pg.font.init()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(0.1)
        # 日本語対応フォントの読み込み
        self.font_path = resource_path("client/assets/fonts/NotoSansJP-Regular.ttf")
        self.jpfont = pg.font.Font(self.font_path, 36)
        self.exit_button_img = pg.image.load(resource_path("client/assets/images/endbotton.png"))
        self.retry_button_img = pg.image.load(resource_path("client/assets/images/trybotton.png"))
        self.help_button_img = pg.image.load(resource_path("client/assets/images/helpbutton.png"))
        self.font = pg.font.SysFont(None, 48)
        self.start_game_time = 0
        self.input_text = ""
        self.role = role
        self.running = True
        self.server_ip = ""#後でタイトルかロビー画面で入力できるようにする
        self.server_port = config.SERVER_PORT
        self.server_addr = None
        self.player_id = None
        self.ip_entered = False
        self.last_send_time = 0
        self.time_limit = 60000
        self.send_interval = 100  # ms
        self.last_state_request_time = pg.time.get_ticks()
        self.state_request_interval = 200  # ms
        self.clock = pg.time.Clock()
        self.state = "lobby"  # 追加: ロビー → ゲームの状態を管理
        # クライアントの画面に表示する全プレイヤーのオブジェクトを管理する辞書
        self.all_players_on_screen = {}
        self.current_player_count = 0 #プレイヤー人数

        # サーバーからのメッセージを待機するスレッド
        threading.Thread(target=self.receive_loop, daemon=True).start()
        image_path2 = resource_path("client/assets/images/momiji.png")
        image_path3 = resource_path("client/assets/images/ido_gray.png")
        image_path4 = resource_path("client/assets/images/iwa_01.png")
        image_path5 = resource_path("client/assets/images/otera.png")
        image_path6 = resource_path("client/assets/images/torii01.png")
        # 障害物画像
        self.obstacle_images = {
            "momiji": pg.transform.scale(pg.image.load(image_path2), (60, 60)),
            "ido": pg.transform.scale(pg.image.load(image_path3), (30, 30)),
            "iwa": pg.transform.scale(pg.image.load(image_path4), (30, 30)),
            "otera": pg.transform.scale(pg.image.load(image_path5), (80, 80)),
            "torii": pg.transform.scale(pg.image.load(image_path6), (80, 80))
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
        
        self.result_shown = False  # 勝敗表示済みフラグ
    def show_help_message(self):
        # tkinterのルートウィンドウを非表示で作成
        root = tk.Tk()
        root.withdraw() # メインウィンドウを表示しないようにする
        # ヘルプメッセージ表示
        messagebox.showinfo("操作方法","WASDで移動します。\n鬼は人間を追いかけてください!\n人間は制限時間まで逃げてください。")
        root.destroy() # 使い終わったら破棄
    # プレイヤーと障害物の当たり判定を確認
    def collides_with_obstacles(self, rect, obstacles):
        for obs in obstacles:
            # pos を元に Rect を作成（仮に 50x50 サイズなら）
            obs_rect = pg.Rect(obs["pos"][0], obs["pos"][1], 50, 50)
            if rect.colliderect(obs_rect):
                return True
        return False
    # IPアドレス入力画面の描画
    def draw_ip_input(self):
        screen.fill((30, 30, 30))
        
        title = self.jpfont.render("接続先IPアドレスを入力 (Enterで確定)", True, (255, 255, 255))
        input_surface = self.font.render(self.server_ip, True, (0, 255, 0))
        screen.blit(titleimg, (0, 0))
        screen.blit(title, (100, 200))
        screen.blit(input_surface, (100, 300))
        self.help_button_img = pg.transform.scale(self.help_button_img, (150, 80))
        self.help_button_rect = self.help_button_img.get_rect(topleft=(650, 0))
        screen.blit(self.help_button_img, self.help_button_rect)
        pg.display.flip()

    # ゲーム開始待機ロビー画面
    def draw_lobby(self):
        screen.blit(lobbyimg, (0, 0))
        # font = pg.font.SysFont(None, 40)
        self.socket.sendto(b"get_player_count", self.server_addr)
        # data,addr = self.socket.recvfrom(1024)
        # received_data = json.loads(data.decode())
        # p_count = received_data.get("player_count", 0)
        max_players = 4  # 最大プレイヤー数
        
        text = self.jpfont.render(f"待機:{self.current_player_count}/{max_players}", True, (255, 255, 255))
        screen.blit(text, (100, 250))
        # screen.blit(text, (100, 250))

        pg.display.flip()

    # ロビーでのIP入力ループ
    def lobby_loop(self):
        while not self.ip_entered:
            self.draw_ip_input()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if self.help_button_rect.collidepoint(event.pos):
                        self.show_help_message()
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_RETURN:
                        self.ip_entered = True
                        self.send_connect_request()
                    elif event.key == pg.K_BACKSPACE:
                        self.server_ip = self.server_ip[:-1]
                    else:
                        # 数字、ドットなど入力可能な文字のみ
                        if len(self.server_ip) < 15 and event.unicode.isprintable():
                            self.server_ip += event.unicode

            
    # サーバーへの接続要求を送る
    def send_connect_request(self):
        self.server_addr = (self.server_ip, self.server_port)
        connect_msg = {
            "type": "connect_request",
            "name": "Player"
            }
        self.socket.sendto(json.dumps(connect_msg).encode(), self.server_addr)
        print("[送信] connect_request を送信しました")
        # try:
        #     data, _ = self.socket.recvfrom(1024)
        #     response = json.loads(data.decode())
        #     if response.get("type") == "connect_ack":
        #         self.player_id = response["player_id"]
        #         print(f"[接続成功] プレイヤーID: {self.player_id}")
        #         # self.state = "lobby"  # ← これがないとdraw_lobbyが呼ばれない
        #     else:
        #         print("[警告] サーバーから未知の応答:", response)
                
        # except socket.timeout:
        #     print("[接続失敗] サーバーから応答なし")

    # サーバーからのメッセージ受信ループ
    def receive_loop(self):
        while self.running:
            try:
                data, _ = self.socket.recvfrom(2048)
                message = json.loads(data.decode())
                now = pg.time.get_ticks()

                msg_type = message.get("type")
                if msg_type == "connect_ack":
                    self.player_id = message["player_id"]
                    print(f"[接続成功] プレイヤーID: {self.player_id}")
                    
                elif msg_type == "player_count_update":
                    self.current_player_count = message.get("player_count", 0)

                elif msg_type == "start_game":
                    print("[🎮] ゲーム開始シグナル受信")
                    self.state = "playing"
                    self.start_game_time = pg.time.get_ticks()
                    #self.draw_lobby() #ロビー画面に移動
                    # self.draw()  # マップ画面に遷移するメソッド

                elif msg_type == "game_state":
                    self.players = message["players"]
                    for pid, pdata in self.players.items():
                        if pid not in self.all_players_on_screen:
                            p = Player(pdata["role"], pdata["pos"][0], pdata["pos"][1])
                            self.all_players_on_screen[pid] = p
                        else:
                            p = self.all_players_on_screen[pid]
                            if p.role == "oni":
                                p.onirect.topleft = pdata["pos"]
                            else:
                                p.chararect1.topleft = pdata["pos"]

                elif msg_type == "game_result":
                    winner = message.get("winner")
                    self.state = "result"
                    self.show_result(winner)


                else:
                    print(f"[警告] サーバーから未知の応答: {message}")

            except socket.timeout:
                continue
            except Exception as e:
                print("[受信エラー]", e)

    # 結果表示
    def show_result(self, winner):
        # screen.fill((0, 0, 0))  # 画面を黒に塗りつぶし

        font = pg.font.SysFont(None, 64)
        if winner == "oni":
            text = self.jpfont.render("鬼の勝利！", True, (255, 0, 0))
        else:
            text = self.jpfont.render("人間の勝利！", True, (0, 255, 0))

        screen.blit(text, (320, 200))  # 適当な位置に表示
        # ボタン設定
        # スケーリング
        self.exit_button_img = pg.transform.scale(self.exit_button_img, (150, 80))
        self.retry_button_img = pg.transform.scale(self.retry_button_img, (150, 80))
        # ボタンの Rect を作成して位置を指定（画面中央あたり）
        self.exit_button_rect = self.exit_button_img.get_rect(center=(config.SCREEN_WIDTH // 2, 350))
        self.retry_button_rect = self.retry_button_img.get_rect(center=(config.SCREEN_WIDTH // 2, 450))
        # ボタン画像の表示
        screen.blit(self.exit_button_img, self.exit_button_rect)
        screen.blit(self.retry_button_img, self.retry_button_rect)
        pg.display.flip()
         # ボタン待ちループ
        waiting = True
        while waiting:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if self.exit_button_rect.collidepoint(event.pos):
                        pg.quit()
                        sys.exit()
                    elif self.retry_button_rect.collidepoint(event.pos):
                        waiting = False  # 再スタート用に break
            self.clock.tick(60)
    # ゲーム画面の描画
    def draw(self):
        screen.blit(haikeimg, (0, 0))
        # 障害物の描画
        for obs in self.obstacles:
            img = self.obstacle_images.get(obs["type"])
            if img:
                screen.blit(img, obs["pos"])
        # 全プレイヤーの描画（IDごと）
        for pid, player in self.all_players_on_screen.items():
            if player.role == "oni":
                screen.blit(player.oni_image, player.onirect)
            else:
                screen.blit(player.player_image, player.chararect1)
        # 残り時間の表示
        if hasattr(self, "start_game_time") and hasattr(self, "time_limit"):
            elapsed = pg.time.get_ticks() - self.start_game_time
            remaining = max(0, (self.time_limit - elapsed) // 1000)
            font = pg.font.SysFont(None, 36)
            timer_text = self.jpfont.render(f"残り時間: {remaining} 秒", True, (255, 255, 255))
            screen.blit(timer_text, (10, 10))
        pg.display.flip()

    # タイトルの表示
    def draw_title(self):
        # タイトル画面(仮)
        self.handle_common_events()
        self.state = "title"  # タイトル状態に設定
        screen.blit(titleimg, (0, 0))
        screen.fill((60, 20, 20))
        font = pg.font.SysFont(None, 40)
        text = font.render("ONI LINK", True, (255,255,255))
        
        screen.blit(text,(100,250))
        pg.display.flip()
    # 結果表示(おそらく現在使われていない)
    def draw_result(self):
        self.state = "result"  # 結果状態に設定
        screen.fill((20,60,20))
        font = pg.font.SysFont(None,40)
        text = font.render("OOteam Victory!", True,(255,255,255))
        screen.blit(text,(100,250))
        pg.display.flip()
    # キーボード操作など
    def handle_player_movement(self):
        keys = pg.key.get_pressed()
        my_player = self.all_players_on_screen.get(self.player_id)
        if not my_player:
            return

        moved = False
        speed = Player.oni_speed if my_player.role == "oni" else Player.player_speed
        rect = my_player.onirect if my_player.role == "oni" else my_player.chararect1

        # 現在の座標を保存
        original_pos = rect.topleft

        # 新しい座標を計算
        if keys[pg.K_w]:
            rect.y -= speed
            moved = True
        if keys[pg.K_s]:
            rect.y += speed
            moved = True
        if keys[pg.K_a]:
            rect.x -= speed
            moved = True
        if keys[pg.K_d]:
            rect.x += speed
            moved = True
        # すでに全プレイヤーの描画情報が self.all_players_on_screen にある前提
        if self.state == "playing":
            my_player = self.all_players_on_screen.get(self.player_id)
            if my_player and my_player.role == "oni":
                oni_rect = my_player.onirect

                for pid, other_player in self.all_players_on_screen.items():
                    if pid == self.player_id:
                        continue  # 自分自身はスキップ
                    if other_player.role == "runner":
                        runner_rect = other_player.chararect1
                        if oni_rect.colliderect(runner_rect):
                            print("👹 鬼がランナーを捕まえた！")

                            self.state = "result"
                            self.show_result("oni")
                            msg = {"type": "game_result", "winner": "oni"}
                            self.socket.sendto(json.dumps(msg).encode(), self.server_addr)
                            return  # 勝利後は移動処理を終了
        # 当たり判定チェック
        if moved and self.collides_with_obstacles(rect, self.obstacles):
            # 衝突していたら元の位置に戻す
            rect.topleft = original_pos
            moved = False  # 移動キャンセル

        if moved:
            pos = [rect.x, rect.y]
            update_msg = {
                "type": "position_update",
                "player_id": self.player_id,
                "pos": pos
            }
            try:
                self.socket.sendto(json.dumps(update_msg).encode(), self.server_addr)
                print(f"[送信] 新しい位置: {pos}")
            except Exception as e:
                print("[送信エラー]", e)
    # ウィンドウを閉じる処理(それぞれの場所で同じ処理が書かれていることが多いので使わなくてもよい)
    def handle_common_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
    # 座標の送信
    def send_position_update(self, pos):
        try:
            update_msg = {
                "type": "position_update",
                "player_id": self.player_id,
                "pos": pos
            }
            self.socket.sendto(json.dumps(update_msg).encode(), self.server_addr)
        except Exception as e:
            print("[位置送信エラー]", e)
    # すべてのプレイヤーの座標更新
    def update_all_players(self):
        self.all_players_on_screen.clear()
        for pid, pdata in self.players.items():
            role = pdata.get("role", "runner")
            x, y = pdata.get("pos", [100, 100])
            player = Player(role, x, y)
            self.all_players_on_screen[pid] = player
    # WASDのどのキーが押されたか送信
    def send_move_command(self, direction):
        msg = {
            "type": "move",
            "direction": direction  # e.g. "up", "down", "left", "right"
        }
        self.socket.sendto(json.dumps(msg).encode(), self.server_addr)
    # メインループ
    def run(self):
        while not self.ip_entered:
            self.lobby_loop()  # IP入力画面のループ
        # self.state = "lobby"

        last_send_time = pg.time.get_ticks()
        send_interval = 100

        while self.running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
                    
            current_time = pg.time.get_ticks()
            
            if self.state == "lobby":
                self.draw_lobby() # ロビー画面に移動
                # プレイヤー数更新要求を定期的に送信
                if current_time - self.last_state_request_time > self.state_request_interval:
                    try:
                        msg = {"type": "get_player_count_request"}
                        self.socket.sendto(json.dumps(msg).encode(), self.server_addr)
                        self.last_state_request_time = current_time
                    except Exception as e:
                        print(f"[送信エラー] ロビー更新要求: {e}")
            elif self.state == "playing" and current_time - last_send_time > send_interval:
                try:
                    msg = {"type": "state_request"}
                    self.socket.sendto(json.dumps(msg).encode(), self.server_addr)
                    last_send_time = current_time
                except Exception as e:
                    print("[送信エラー]", e)

            if self.state == "playing":
                self.handle_player_movement()
                self.draw()
                elapsed = pg.time.get_ticks() - self.start_game_time
                if elapsed >= self.time_limit:
                    self.state = "result"
                    self.show_result("runner")
                    msg = {"type": "game_result", "winner": "runner"}
                    self.socket.sendto(json.dumps(msg).encode(), self.server_addr)
            elif self.state == "result":
                pass

            self.clock.tick(60)
            
if __name__ == "__main__":
    game = Game()
    game.run()
