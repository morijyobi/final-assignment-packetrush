# game.py
#ソケットの通信の準備、プレイヤー情報の送受信など
import pygame as pg, sys
import socket
import json
import threading
from client.player import Player
from client.utils import config
import os
from pygame import mixer
import ipaddress
import tkinter as tk
from tkinter import messagebox
import traceback
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
        pg.mixer.init()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(0.1)
        # 日本語対応フォントの読み込み
        self.font_path = resource_path("client/assets/fonts/NotoSansJP-Regular.ttf")
        self.jpfont = pg.font.Font(self.font_path, 36)
        self.player_name_font = pg.font.Font(self.font_path, 18)
        self.player_name = ""
        self.input_mode = "ip" # ipまたはnameのどちらか
        self.exit_button_img = pg.image.load(resource_path("client/assets/images/endbotton.png"))
        self.retry_button_img = pg.image.load(resource_path("client/assets/images/trybotton.png"))
        self.help_button_img = pg.image.load(resource_path("client/assets/images/helpbutton.png"))
        self.title_button_img = pg.image.load(resource_path("client/assets/images/titlebutton.png"))
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
        self.winner = None # ← 勝者情報を初期化
        self.receive_thread = None
        self.state = "mode_select"  # 起動直後はモード選択画面
        self.mode = None # "local"または"online"を保持
        self.game_mode = "normal" # または"escape"
        goal_img_path = resource_path("client/assets/images/goal.png")
        self.goal_image = pg.transform.scale(pg.image.load(goal_img_path), (60, 60)) # サイズ調整
        self.goal_pos = (600, 100)
        self.goal_rect = pg.Rect(self.goal_pos[0], self.goal_pos[1], 60, 60)
        # クライアントの画面に表示する全プレイヤーのオブジェクトを管理する辞書
        self.all_players_on_screen = {}
        self.current_player_count = 0 #プレイヤー人数
        self.ip_error_message = ""
        
        self.game_bgm_path = resource_path("client/assets/sounds/立待ち月.mp3") # bgm
        self.lobby_bgm_path = resource_path("client/assets/sounds/華ト月夜.mp3")
        self.current_bgm_path = None

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
            "iwa": pg.transform.scale(pg.image.load(image_path4), (20, 20)),
            "otera": pg.transform.scale(pg.image.load(image_path5), (80, 80)),
            "torii": pg.transform.scale(pg.image.load(image_path6), (80, 80))
        }

        # 障害物データ
        self.obstacles = [
            {"type": "momiji", "pos": (230, 180), "width": 50, "height":50},# 高さと横幅を追加
            {"type": "momiji", "pos": (230, 260), "width": 50, "height":50},
            {"type": "momiji", "pos": (230, 340), "width": 50, "height":50},
            {"type": "otera", "pos": (380, 50), "width": 65, "height":50},
            {"type": "torii", "pos": (383, 130), "width": 55, "height":40},
            {"type": "iwa", "pos": (350, 250), "width": 15, "height":15},
            {"type": "iwa", "pos": (450, 330), "width": 15, "height":15},
            {"type": "ido", "pos": (500, 90), "width": 15, "height":15},
            {"type": "momiji", "pos": (530, 180), "width": 50, "height":50},
            {"type": "momiji", "pos": (530, 260), "width": 50, "height":50},
            {"type": "momiji", "pos": (530, 340), "width": 50, "height":50}
        ]
        self.obstacle_rects = []
        for obs in self.obstacles:
            x, y = obs["pos"]
            obj_type = obs["type"]
            if obj_type == "momiji":
                width, height = 50, 50
            elif obj_type == "otera":
                width, height = 80, 80
            elif obj_type == "torii":
                width, height = 80, 80
            elif obj_type == "iwa":
                width, height = 16, 16
            elif obj_type == "ido":
                width, height = 30, 30 # 念のためデフォルト
            else:
                width, height = 30, 30
            rect = pg.Rect(x, y, width, height)
            self.obstacle_rects.append(rect)
        self.result_shown = False  # 勝敗表示済みフラグ
    def restart_receive_loop(self):
        # すでにスレッドが動いているか確認して止まっていたら再起動
        if not self.receive_thread or not self.receive_thread.is_alive():
            self.running = True
            self.receive_thread = threading.Thread(target=self.receive_loop, daemon=True)
            self.receive_thread.start()
            print("receive_loop を再起動しました")
        else:
            print("receive_loop はすでに実行中です")

    def reset_game_state(self):
    # ゲームの状態変数を初期値にリセット
        self.players = {}
        self.all_players_on_screen = {}
        self.start_game_time = 0
        self.input_text = ""
        self.running = True
        self.player_id = None
        self.ip_entered = False
        self.last_send_time = 0
        self.last_state_request_time = pg.time.get_ticks()
        self.current_player_count = 0
        self.ip_error_message = ""
        self.result_shown = False
        self.result_winner = None
        self.mode = None  # ローカル・オンライン問わずリセット
        self.server_ip = ""  # IPをリセット
        self.player_name = ""  # 名前もリセット

        if hasattr(self, "local_initialized"):
            del self.local_initialized
        if hasattr(self, "ai_id"):
            del self.ai_id
        # 各プレイヤーのescape/caught状態を初期化
        for player in self.all_players_on_screen.values():
            if hasattr(player, "escaped"):
                player.escaped = False
            if hasattr(player, "caught"):
                player.caught = False
        # 状態を戻す
        if self.mode == "online":
            self.state = "input_ip"
            if self.player_id:
                disconnect_msg = {"type": "disconnect", "player_id": self.player_id}
                self.socket.sendto(json.dumps(disconnect_msg).encode(), self.server_addr)
        else:
            self.state = "mode_select"
        print("[ゲームリセット] ゲーム状態が初期化されました。")
        self.winner = None # 勝者状態を完全リセット
    def handle_title_events(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.toggle_mode_rect.collidepoint(event.pos):
                # モードを切り替え
                self.game_mode = "escape" if self.game_mode == "normal" else "normal"
                print(f"モード切替:{self.game_mode}")
    def check_collision(self, rect):
        for obstacle in self.obstacle_rects:
            if rect.colliderect(obstacle):
                print("衝突しました")
                return True
        return False
    def update_ai_movement(self):
        print(f"update_ai_movement called with state={self.state}")
        if self.state not in ["play_local", "playing"]:
            print(f"update_ai_movement: state = {self.state}, returning")
            return
        ai_player = self.all_players_on_screen.get(self.ai_id)
        runner = self.all_players_on_screen.get(self.player_id)
        if not ai_player or not runner:
            print("update_ai_movement: ai_player or runner not found")
            return

        speed = 2
        moved = False

        directions = []

        # X方向の移動方向を決める
        if ai_player.onirect.x < runner.chararect1.x:
            directions.append((speed, 0))
        elif ai_player.onirect.x > runner.chararect1.x:
            directions.append((-speed, 0))

        # Y方向の移動方向を決める
        if ai_player.onirect.y < runner.chararect1.y:
            directions.append((0, speed))
        elif ai_player.onirect.y > runner.chararect1.y:
            directions.append((0, -speed))
        if not directions:
            print("update_ai_movement: no directions to move")
            return
        original_pos = ai_player.onirect.topleft
        print(f"update_ai_movement: directions={directions}, original_pos={original_pos}")
        for move_x, move_y in directions:
            ai_player.onirect.x += move_x
            ai_player.onirect.y += move_y
            collision = self.check_collision(ai_player.onirect)
            print(f"Trying move ({move_x}, {move_y}), collision={collision}")
            if not collision:
                moved = True
                break
            else:
                ai_player.onirect.topleft = original_pos

        if not moved:
            # 衝突で動けなければ元の位置に戻す
            ai_player.onirect.topleft = original_pos

        # 当たり判定(鬼がランナーを捕まえた)
        if ai_player.onirect.colliderect(runner.chararect1):
            pg.mixer.Sound(resource_path("client/assets/sounds/倒れる.mp3"))
            print("AI鬼に捕まりました!")
            self.state = "result"
            self.show_result("oni")
        print(f"AI位置: {ai_player.onirect.topleft}")
    def play_local_game(self):
        # 初期化済みか確認
        if not hasattr(self, "local_initialized") or not self.local_initialized:
            self.player_id = "local_player"
            self.all_players_on_screen[self.player_id] = Player("runner", 100, 100, "自分")
            self.ai_id = "ai_oni"
            self.all_players_on_screen[self.ai_id] = Player("oni", 0, 300, "鬼ボット")
            self.start_game_time = pg.time.get_ticks()
            self.state = "playing" # プレイ状態に移行
            self.local_initialized = True # フラグを立てて初期化を1回だけにする
        screen.fill((0, 0, 0))
        self.handle_player_movement() # プレイヤーの操作
        print(f"play_local_game: state = {self.state}")
        self.update_ai_movement() # AIの自動移動
        print(f"update_ai_movement: state = {self.state}")
        self.draw() # ゲーム画面描画
    def draw_mode_select(self):
        screen.fill((30, 30, 30))
        title = self.jpfont.render("モード選択", True, (255, 255, 255))
        local_btn = self.jpfont.render("1人で遊ぶ", True, (0, 255, 0))
        online_btn = self.jpfont.render("オンライン対戦", True, (0, 255, 255))
        # ボタンの位置と範囲(selfに保存しておく)
        self.local_btn_rect = local_btn.get_rect(topleft=(300, 200))
        self.online_btn_rect = online_btn.get_rect(topleft=(300, 300))
        screen.blit(title, (300, 100))
        screen.blit(local_btn, self.local_btn_rect.topleft)
        screen.blit(online_btn, self.online_btn_rect.topleft)
        pg.display.flip()
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
            #  obstaclesのwidthとheightを元に Rect を作成
            obs_rect = pg.Rect(obs["pos"][0], obs["pos"][1], obs["width"], obs["height"])
            if rect.colliderect(obs_rect):
                return True
        return False
    # IPアドレス入力画面の描画
    def draw_ip_input(self):
        screen.fill((30, 30, 30))
        explanation = self.jpfont.render("TABキーで入力する項目変更、Enterで確定", True, (255, 255, 255))
        ip_color = (0, 255, 0) if self.input_mode == "ip" else (100, 100, 100)
        name_color = (0, 255, 255) if self.input_mode == "name" else (100, 100, 100)
        # ラベル
        title = self.jpfont.render("接続先IPアドレス", True, ip_color)
        title_name = self.jpfont.render("プレイヤー名", True, name_color)
        # 入力内容
        input_surface = self.font.render(self.server_ip, True, (0, 255, 0))
        name_surface = self.font.render(self.player_name, True, (0, 255, 255))
        # 表示位置
        screen.blit(titleimg, (0, 0))
        screen.blit(explanation, (50, 170))
        screen.blit(title, (100, 250))
        screen.blit(input_surface, (100, 300))
        screen.blit(title_name, (100, 350))
        screen.blit(name_surface, (100, 400))
        # モードトグルボタン
        mode_text = "現在のモード:ノーマル" if self.game_mode == "normal" else "現在のモード:脱出"
        mode_explanation_text = "クリックでモード変更"
        mode_explanation_font = pg.font.Font(self.font_path, 24)
        self.toggle_mode_rect = pg.Rect(250, 0, 400, 60)
        pg.draw.rect(screen, (50, 150, 200), self.toggle_mode_rect)
        mode_surface = self.jpfont.render(mode_text, True, (255, 255, 255))
        mode_explanation_surface = mode_explanation_font.render(mode_explanation_text, True, (255, 255, 255))
        screen.blit(mode_surface, (self.toggle_mode_rect.x + 5, self.toggle_mode_rect.y + 8))
        screen.blit(mode_explanation_surface, (4, 0))
        # エラーメッセージ表示
        if self.ip_error_message:
            error_text = self.jpfont.render(self.ip_error_message, True, (255, 0, 0)) # 赤色で表示
            screen.blit(error_text, (100, 210))
        # ヘルプボタン
        self.help_button_img = pg.transform.scale(self.help_button_img, (150, 80))
        self.help_button_rect = self.help_button_img.get_rect(topleft=(650, 0))
        screen.blit(self.help_button_img, self.help_button_rect)
        self.title_button_img = pg.transform.scale(self.title_button_img, (250, 100))
        self.title_button_rect = self.title_button_img.get_rect(topleft=(300, 450))
        screen.blit(self.title_button_img, self.title_button_rect)
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
                    if self.title_button_rect.collidepoint(event.pos):
                        self.ip_entered = True
                        self.send_connect_request()
                    # モード切り替えボタンの判定
                    self.handle_title_events(event)
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_TAB:
                        # TABキーで入力対象を切り替える
                        self.input_mode = "name" if self.input_mode == "ip" else "ip"
                    elif event.key == pg.K_RETURN:
                        if self.server_ip and self.player_name:
                            self.ip_entered = True
                            self.send_connect_request()
                    elif event.key == pg.K_BACKSPACE:
                        if self.input_mode == "ip":
                            self.server_ip = self.server_ip[:-1]
                        else:
                            self.player_name = self.player_name[:-1]
                    else:
                        # 数字、ドットなど入力可能な文字のみ
                        if event.unicode.isprintable():
                            if self.input_mode == "ip" and len(self.server_ip) < 15:
                                self.server_ip += event.unicode
                            elif self.input_mode == "name" and len(self.player_name) < 12:
                                self.player_name += event.unicode

            
    # サーバーへの接続要求を送る
    def send_connect_request(self):
        self.ip_error_message = "" # 新しい接続試行時にエラーメッセージをリセット
        try:
            ipaddress.ip_address(self.server_ip)
        except ValueError:
            self.ip_error_message = "IPアドレスの形式が不正です！"
            self.ip_entered = False
            return
        self.server_addr = (self.server_ip, self.server_port)
        connect_msg = {
            "type": "connect_request",
            "name": self.player_name or "Player",
            "game_mode": self.game_mode # ←"escape" or "normal"
            }
        try:
            self.socket.sendto(json.dumps(connect_msg).encode(), self.server_addr)
            print("[送信] connect_request を送信しました")
        except Exception as e:
            self.ip_error_message = f"サーバーへの接続に失敗しました: {e}"
            self.ip_entered = False
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
        print("[スレッド] receive_loop 開始")
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
                    print(f"[DEBUG] 状態を playing に設定しました (state = {self.state})")
                    #self.draw_lobby() #ロビー画面に移動
                    # self.draw()  # マップ画面に遷移するメソッド

                elif msg_type == "game_state":
                    self.players = message["players"]
                    for pid, pdata in self.players.items():
                        name = pdata.get("name", f"Player{pid[:4]}") # 名前を取得
                        caught = pdata.get("caught", False)
                        escaped = pdata.get("escaped", False)
                        if pid not in self.all_players_on_screen:
                            p = Player(pdata["role"], pdata["pos"][0], pdata["pos"][1], name, caught)
                            p.caught = caught
                            p.escaped = escaped
                            self.all_players_on_screen[pid] = p
                            
                        else:
                            p = self.all_players_on_screen[pid]
                            if p.role == "oni":
                                p.onirect.topleft = pdata["pos"]
                            else:
                                p.chararect1.topleft = pdata["pos"]
                            p.escaped = escaped # 毎回上書き
                            p.caught = caught # 毎回上書きする
                elif msg_type == "game_result":
                    print("[受信]勝者情報を受信:", message)
                    self.winner = message.get("winner")
                    self.state = "result"
                    self.show_result(self.winner)
                    print("[受信] 勝者情報を受信:", message)
                elif msg_type == "retry_start":
                    self.result_shown = False
                    self.state = "lobby"
                    self.running = True
                    self.all_players_on_screen.clear()
                    self.players.clear()
                    self.draw_lobby()
                    self.restart_receive_loop()
                else:
                    print(f"[警告] サーバーから未知の応答: {message}")

            except socket.timeout:
                continue
            except Exception as e:
                print("[受信エラー]", e)

    # 結果表示
    def show_result(self, winner):
        # screen.fill((0, 0, 0))  # 画面を黒に塗りつぶし
        
        # bgm停止
        if pg.mixer.music.get_busy():
            pg.mixer.music.stop()
            self.current_bgm_path = None

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
                    print("Click pos:", event.pos)
                    if self.exit_button_rect.collidepoint(event.pos):
                        # ゲーム終了
                        msg = {"type": "game_end"}
                        try:
                            self.socket.sendto(json.dumps(msg).encode(), self.server_addr)
                            print("ゲームエンドのメッセージ")
                        except Exception as e:
                            print("ゲームエンドのメッセージのエラー")
                        pg.quit()
                        sys.exit()
                    # もう一度ボタンのクリックイベント処理
                    elif self.retry_button_rect.collidepoint(event.pos):
                        if self.server_addr:
                            print("[🔁] 再試合希望を送信")
                            msg = {"type": "retry_request", "player_id": self.player_id}
                            self.socket.sendto(json.dumps(msg).encode(), self.server_addr)
                        self.reset_game_state()
                        if self.mode == "local": 
                            self.state = "mode_select" # 一人で遊んだ場合 → モード選択画面に戻る
                        elif self.mode == "online":
                            self.state = "input_ip" # オンラインの場合 → IPアドレス入力画面に戻る
                            self.ip_entered = False
                            # 再接続要求を送る
                            self.send_connect_request()
                        waiting = False
            pg.time.delay(100)  # CPUへの負荷軽減

            self.clock.tick(60)
        # show_result を抜けた後、run メソッドのループが継続し、
        # リセットされた state に基づいて画面が描画される
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
            if hasattr(self, "players") and pid in self.players:
                player_data = self.players[pid]
                name = player_data.get("name", "")
                name_surface = self.player_name_font.render(name, True, (255, 255, 255))
                name_pos = (player.chararect1.x + 6, player.chararect1.y - 20) if player.role == "runner" else (player.onirect.x + 6, player.onirect.y - 20)
                screen.blit(name_surface, name_pos)
            # キャラ画像の描画(元々ある部分)
            if player.role == "oni":
                screen.blit(player.oni_image, player.onirect)
            else:
                if getattr(player, "caught", False):
                    continue
                screen.blit(player.player_image, player.chararect1)
        # 残り時間の表示
        if hasattr(self, "start_game_time") and hasattr(self, "time_limit"):
            elapsed = pg.time.get_ticks() - self.start_game_time
            remaining = max(0, (self.time_limit - elapsed) // 1000)
            font = pg.font.SysFont(None, 36)
            timer_text = self.jpfont.render(f"残り時間: {remaining} 秒", True, (255, 255, 255))
            screen.blit(timer_text, (10, 10))
        if self.game_mode == "escape":
            screen.blit(self.goal_image, self.goal_pos)
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
        original_pos = rect.topleft

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

        # 画面外に行かせない
        if rect.y < 0:
            rect.y = 0
        if rect.y > config.SCREEN_HEIGHT - rect.height:
            rect.y = config.SCREEN_HEIGHT - rect.height
        if rect.x < 0:
            rect.x = 0
        if rect.x > config.SCREEN_WIDTH - rect.width:
            rect.x = config.SCREEN_WIDTH - rect.width

        # --- 当たり判定: 鬼がランナーを捕まえた場合 ---
        if self.state == "playing" and my_player.role == "oni":
            oni_rect = my_player.onirect
            for pid, other_player in self.all_players_on_screen.items():
                if pid == self.player_id or other_player.role != "runner":
                    continue
                runner_rect = other_player.chararect1
                if oni_rect.colliderect(runner_rect):
                    if not getattr(other_player, "caught", False):
                        print("👹 鬼がランナーを捕まえた！")
                        pg.mixer.Sound(resource_path("client/assets/sounds/倒れる.mp3"))
                        other_player.caught = True  # 捕まった印
            # すべてのランナーが caught なら勝利
            runners = [p for p in self.all_players_on_screen.values() if p.role == "runner"]
            all_caught = all(getattr(r, "caught", False) for r in runners)
            # print("ランナーの状態:")
            # for r in runners:
            #     print(f"  - {getattr(r, 'name', '')}: caught={getattr(r, 'caught', False)}")
            if runners and all_caught:
                print("👹 すべてのランナーが捕まりました！鬼の勝利！")
                msg = {"type": "game_result", "winner": "oni"}
                self.socket.sendto(json.dumps(msg).encode(), self.server_addr)
                self.winner = "oni"
                self.state = "result"
                return

        # ゴール到達チェック（逃走モード）
        if self.game_mode == "escape" and hasattr(self, "goal_rect"):
            if rect.colliderect(self.goal_rect) and my_player.role != "runner":
                rect.topleft = original_pos
                moved = False

        # 障害物との衝突
        if moved and self.collides_with_obstacles(rect, self.obstacles):
            rect.topleft = original_pos
            moved = False

        # ランナーがゴールに到達
        if self.game_mode == "escape" and my_player.role == "runner":
            if rect.colliderect(self.goal_rect) and not getattr(my_player, "escaped", False):
                if not getattr(my_player, "escaped", False):
                    print("ランナーがゴールに到達！")
                    my_player.escaped = True # このプレイヤーは脱出済みにする
                    # サーバーに「脱出済み」を伝える
                    if self.mode == "online":
                        msg = {
                            "type": "escaped",
                            "player_id": self.player_id
                        }
                        self.socket.sendto(json.dumps(msg).encode(), self.server_addr)
                # ランナーの一覧を取得
                runners = [
                    p for p in self.all_players_on_screen.values()
                    if p.role == "runner"
                ]
                # 脱出したランナー数の確認
                escaped_count = 0
                for r in runners:
                    if getattr(r, "escaped", False):
                        escaped_count += 1
                print(f"[チェック]脱出済みランナー数:{escaped_count}/{len(runners)}")
                # 全員がゴールしたかチェック
                if escaped_count == len(runners) and len(runners) > 0:
                    print("全ランナーが脱出!人間の勝利!")
                    self.state = "result"
                    self.show_result("runner") # 人間の勝利
                    if self.mode == "online":
                        msg = {"type": "game_result", "winner": "runner"}
                        self.socket.sendto(json.dumps(msg).encode(), self.server_addr)
                # return

        # 位置更新を送信
        if moved:
            pos = [rect.x, rect.y]
            update_msg = {
                "type": "position_update",
                "player_id": self.player_id,
                "pos": pos
            }
            try:
                if self.mode == "online":
                    self.socket.sendto(json.dumps(update_msg).encode(), self.server_addr)
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
        # while not self.ip_entered:
        #     self.lobby_loop()  # IP入力画面のループ
        # self.state = "lobby"

        last_send_time = pg.time.get_ticks()
        send_interval = 100

        while self.running:
            # bgmの制御
            target_bgm_path = None
            if self.state == "lobby":
                target_bgm_path = self.lobby_bgm_path
            elif self.state in ["playing", "play_local"]:
                target_bgm_path = self.game_bgm_path
            if target_bgm_path and self.current_bgm_path != target_bgm_path:
                try:
                    pg.mixer.music.load(target_bgm_path)
                    pg.mixer.music.play(-1)
                    self.current_bgm_path = target_bgm_path
                except pg.error as e:
                    print(f"bgmの再生失敗:{e}")
                    self.current_bgm_path = None
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
                # 状態に応じて処理分岐
                if self.state == "mode_select":
                    if event.type == pg.MOUSEBUTTONDOWN:
                        if self.local_btn_rect.collidepoint(event.pos):
                            self.mode = "local"
                            self.state = "play_local" # ローカルモードへ
                        elif self.online_btn_rect.collidepoint(event.pos):
                            self.mode = "online"
                            self.state = "input_ip" # オンラインモードへ
            current_time = pg.time.get_ticks()
            if self.state == "mode_select":
                self.draw_mode_select()
            elif self.state == "input_ip":
                while not self.ip_entered:
                    self.lobby_loop()
                self.state = "lobby"
            elif self.state == "play_local":
                self.play_local_game()
                # if event.type == pg.MOUSEBUTTONDOWN:
                #     if self.back_btn_rect.collidepoint(event.pos):
                #         self.state = "mode_select"
            elif self.state == "lobby":
                self.draw_lobby() # ロビー画面に移動
                # プレイヤー数更新要求を定期的に送信
                if current_time - self.last_state_request_time > self.state_request_interval:
                    try:
                        msg = {"type": "get_player_count_request"}
                        self.socket.sendto(json.dumps(msg).encode(), self.server_addr)
                        self.last_state_request_time = current_time
                    except Exception as e:
                        print(f"[送信エラー] ロビー更新要求: {e}")
            elif self.state == "playing":
                print("ゲーム画面を描画中")
                # 通信はオンラインの時だけ実行
                if self.mode == "online" and current_time - last_send_time > send_interval:
                    try:
                        msg = {"type": "state_request"}
                        self.socket.sendto(json.dumps(msg).encode(), self.server_addr)
                        last_send_time = current_time
                    except Exception as e:
                        print("[送信エラー]", e)
                self.handle_player_movement()
                if self.mode == "local":
                    self.update_ai_movement()
                self.draw()
                elapsed = pg.time.get_ticks() - self.start_game_time
                if elapsed >= self.time_limit:
                    self.state = "result"
                    # 🔽 escapeモードのときは鬼の勝ち
                    if self.game_mode == "escape":
                        self.winner = "oni"
                        self.show_result("oni")  # 鬼の勝利(escapeモード)
                        if self.mode == "online":
                            msg = {"type": "game_result", "winner": "oni"}
                            self.socket.sendto(json.dumps(msg).encode(), self.server_addr)
                    else:
                        self.winner = "runner"
                        self.show_result("runner")  # ノーマルモードではランナー勝利
                        if self.mode == "online":
                            msg = {"type": "game_result", "winner": "runner"}
                            self.socket.sendto(json.dumps(msg).encode(), self.server_addr)

            elif self.state == "result":
                if not self.result_shown and self.winner:
                    self.result_shown = True
                    self.show_result(self.winner)
                    self.state = "mode_select"
            # self.result_shown = False # この行を削除
            self.clock.tick(60)

    
try:
    if __name__ == "__main__":
        game = Game()
        game.run()
except Exception as e:
    with open("error.log", "w") as f:
        traceback.print_exc(file=f)
    import time
    print("エラーが発生しました。error.log を確認してください。")
    time.sleep(5)