import socket
import json
import uuid
import threading
import time
import pygame as pg
import random
# サーバーソケット初期化
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(("0.0.0.0", 5000))
server_socket.settimeout(0.5)
retry_votes = set()  # 再試合希望者のIDを保存
items = {
    "item_001": {"id": "item_1", 
                 "type": "speed", 
                 "pos": [300, 400], 
                 "active": True,
                 "respawn_time": 0 # 秒単位のUNIx時間
                 },
    "item_002": {"id": "item_2",
                 "type": "speed", 
                 "pos": [500, 200], 
                 "active": True,
                 "respawn_time": 0}
}
players = {}
REQUIRED_PLAYERS = 4
game_started = False
game_mode = "normal"
escaped_players = set()
print("サーバー起動: 0.0.0.0:5000 で待機中...")
def update_items():
    now = int(time.time() * 1000) # ミリ秒単位のUNIX時間
    for item in items.values():
        if not item["active"] and now >= item["respawn_time"]:
            item["active"] = True
            print(f"[再出現]{item['id']}が復活しました")
# プレイヤーをアドレスで検索
def find_player_by_addr(addr):
    for pid, player in players.items():
        if player["addr"] == addr:
            return player
    return None
# 押されたキー(WASD)によって座標の変更
def calculate_new_position(pos, direction, step=5):
    x, y = pos
    if direction == "up":
        y -= step
    elif direction == "down":
        y += step
    elif direction == "left":
        x -= step
    elif direction == "right":
        x += step
    return [x, y]
# プレイヤーの初期位置設定
def assign_initial_positions():
    positions_runner = [
        [0, 500],    # 左下
        [720, 100],    # 右上
        [720, 500],  # 右下
    ]
    positions_oni = [
        [0, 100],
    ]

    runner_index = 0
    for pid, p in players.items():
        if p["role"] == "oni":
            p["pos"] = positions_oni[0]  # 鬼は固定位置
        else:
            # ランナーは順番に初期位置を割り当てる
            if runner_index < len(positions_runner):
                p["pos"] = positions_runner[runner_index]
            else:
                # 位置が足りなければ適当に初期化（左下など）
                p["pos"] = [0, 600]
            runner_index += 1
# ✅ クライアントからのメッセージ受信ループ
def receive_loop():
    while True:
        try:
            data, addr = server_socket.recvfrom(1024)
            if not data.strip(): # 空データ対策
                continue
            try:
                message = json.loads(data.decode())
            except json.JSONDecodeError:
                continue
            # ここでmessageだけ渡す
            threading.Thread(target=process_message, args=(message, addr)).start()
            # ここでアイテムの再出現チェックを毎ループ行う
            update_items()
        except socket.timeout:
            # タイムアウト時もupdate_itemsを呼んで再出現チェックを続ける
            update_items()
            continue
        except Exception as e:
            print(f"[受信エラー] {e}")

# ✅ 個別のクライアントメッセージ処理
def process_message(message, addr):
    global game_started
    msg_type = message.get("type")
    
    if msg_type == "connect_request":
        global game_started
        game_started = False
        player_id = str(uuid.uuid4())
        name = message.get("name", "Player")
        if "game_mode" in message:
            global game_mode
            game_mode = message["game_mode"]
            print(f"[モード設定]ゲームモード:{game_mode}")
        players[player_id] = {
            "id": player_id,
            "name": name,
            "pos": [0, 0],
            "addr": addr,
            "role": None,
            "caught": False
        }

        print(f"[接続] {addr} が接続。ID: {player_id}, 名前: {name}")

        
        ack = {"type": "connect_ack", "player_id": player_id}
        server_socket.sendto(json.dumps(ack).encode(), addr)
        # ✅ プレイヤー数が揃ったら、ゲームを開始
        if len(players) >= REQUIRED_PLAYERS and not game_started:
            assign_roles()
            start_game()
    
    elif msg_type == "get_player_count_request":
        # 参加人数を数える
        p_count = len(players)
        response_data = {"type":"player_count_update", "player_count" : p_count}
        server_socket.sendto(json.dumps(response_data).encode(), addr)
        
    elif msg_type == "state_request":
        game_state = {
            "type": "game_state",
            "players": {
                pid: {
                    "id": pid,
                    "name": p["name"],
                    "pos": p["pos"],
                    "role": p["role"],
                    "escaped": p.get("escaped", False),
                    "caught": p.get("caught", False)
                } 
                for pid, p in players.items()
            },
            # アイテム情報を含める
            "items": [
                {
                    "id": item_id,
                    "type": item["type"], 
                    "pos": item["pos"], 
                    "active": item["active"]}
                for item_id, item in items.items()
            ]
        }
        server_socket.sendto(json.dumps(game_state).encode(), addr)
    elif msg_type == "start_game":
        # クライアントから受信することは想定しないが、念のためログだけ
        print("[受信] クライアントからstart_gameメッセージが来ました。無視します。")
    elif msg_type == "position_update":
        player_id = message.get("player_id")
        new_pos = message.get("pos")
        if player_id in players:
            players[player_id]["pos"] = new_pos
            # print(f"[更新] {player_id} の位置を {new_pos} に更新")
            # 脱出チェック(ゴール座標に重なったか)
            if game_mode == "escape": # <-脱出モード限定
                goal_x, goal_y = [600, 100]
                if abs(new_pos[0] - goal_x) < 30 and abs(new_pos[1] - goal_y) < 30:
                    players[player_id]["escaped"] = True
                    print(f"[脱出]{player_id}が脱出しました")
                    # 脱出済みの人数を数える
                    total_runners = sum(1 for p in players.values() if p["role"] == "runner")
                    escaped_runners = sum(1 for p in players.values() if p.get("escaped"))
                    print(f"[チェック]脱出済みランナー数:{escaped_runners}/{total_runners}")
                    if escaped_runners == total_runners:
                        send_game_result("runner") # 全員脱出したので人間勝利
            # 👇 鬼がランナーに接触しているかをチェック（ゲーム開始後のみ）
            if game_started:
                oni_pos = None
                for pid, p in players.items():
                    if p["role"] == "oni":
                        oni_pos = p["pos"]
                        break
                if oni_pos:
                    for pid, p in players.items():
                        if p["role"] == "runner" and not p.get("escaped", False):
                            runner_pos = p["pos"]
                            # 20px以内なら接触とみなす（大きさに合わせて調整）
                            if abs(oni_pos[0] - runner_pos[0]) < 30 and abs(oni_pos[1] - runner_pos[1]) < 30:
                                if not p.get("caught", False):
                                    print(f"[👹接触] 鬼がランナーを捕まえました！")
                                    p["caught"] = True # 捕まったフラグを立てる
                                    # send_game_result("oni")
                                    break
            # アイテムの衝突判定
            if not players[player_id].get("caught", False) and not players[player_id].get("escaped", False):
                for item in items.values():
                    if item["active"]:
                        item_x, item_y = item["pos"]
                        px, py = new_pos
                        # 半径30以内に入ったら取得とみなす
                        if abs(px - item_x) < 30 and abs(py - item_y) < 30:
                            item["active"] = False
                            item["respawn_time"] = int(time.time() * 1000) + 10000 # 10秒後
                            print(f"[アイテム取得]{player_id}が{item['type']}を取得")
        else:
            print(f"[警告] {player_id} は登録されていません")
    elif msg_type == "game_result":
        winner = message.get("winner", "unknown")
        print(f"[結果受信] 勝者: {winner}")

        result_msg = {
            "type": "game_result",
            "winner": winner
        }

        for p in players.values():
            try:
                server_socket.sendto(json.dumps(result_msg).encode(), p["addr"])
            except Exception as e:
                print(f"[送信エラー] {p['id']}: {e}")

        # ✅ 勝敗通知後にゲーム状態をリセット
        game_started = False
    
    elif msg_type == "game_end":
        try:
            game_started = False
            game_end()
        except Exception as e:
            print("error")

    elif msg_type == "retry_request":
        player_id = message.get("player_id")
        if player_id in players:
            retry_votes.add(player_id)
            print(f"[再試合リクエスト] {player_id}")
        
            if len(retry_votes) == len(players):
                print("[再試合] 全員の再試合リクエストが揃いました。ゲームを再開します。")

                retry_votes.clear()

                # まず retry_start を送ってロビーへ戻す
                retry_msg = {"type": "retry_start"}
                for p in players.values():
                    server_socket.sendto(json.dumps(retry_msg).encode(), p["addr"])

                time.sleep(1.0)  # 少し待つ（ロビー描画）

                players.clear()  # ここでクリア（遅らせる）
    elif msg_type == "disconnect":
        player_id = message.get("player_id")
        if player_id in players:
            print(f"[切断]プレイヤー{player_id}が切断しました")
            del players[player_id]
    elif msg_type == "escaped":
        player_id = message.get("player_id")
        if player_id in players:
            escaped_players.add(player_id)
            print(f"[逃走報告]{player_id}が脱出しました")
            total_runners = len([p for p in players.values() if p["role"] == "runner"])
            print(f"[チェック]脱出済みランナー数:{len(escaped_players)}/{total_runners}")
            if len(escaped_players) == total_runners and total_runners > 0:
                print("[全員脱出]人間の勝利")
                send_game_result("runner")
    else:
        print(f"[警告] サーバーから未知の応答: {message}")
# プレイヤーの役割の割り振り
def assign_roles():
    player_ids = list(players.keys())
    if not player_ids:
        return
    oni_id = random.choice(player_ids)   # 先頭を鬼にする（適宜ランダムでも可）

    for pid in player_ids:
        if pid == oni_id:
            players[pid]["role"] = "oni"
        else:
            players[pid]["role"] = "runner"
# ゲーム開始
def start_game():
    global game_started
    game_started = True

    # 役割と初期位置を再設定
    assign_roles()
    assign_initial_positions()

    # 各プレイヤーの再試合同意フラグをリセット
    for p in players.values():
        p["rematch_agreed"] = False

    # 各クライアントにゲーム開始を通知
    start_msg = {"type": "start_game"}
    for pid in players:
        addr = players[pid].get("addr")
        if addr:
            try:
                server_socket.sendto(json.dumps(start_msg).encode(), addr)
                print(f"[送信] start_game メッセージを {p['name']}({pid}) に送信")
            except Exception as e:
                print(f"[送信エラー] {pid}: {e}")

    print("✅ プレイヤーが揃いました。ゲームを開始します。")
 
def game_end():
    global game_started
    global players
    global retry_votes
    global escaped_players
    global game_mode
    print("[サーバー初期化] ゲーム状態とプレイヤー情報をリセット")
    game_started = False
    
    players.clear()# プレイヤー情報を完全にクリア
    retry_votes.clear()
    escaped_players.clear()
    game_mode = "normal"
    print("[サーバー初期化完了] 新しい接続を待機中…")
    # for pid in players:
    #     players[pid]["pos"] = [0, 0] # 初期位置にリセット (または適当な待機位置)
    #     players[pid]["role"] = None # 役割をリセット

def reset_server_game():
    global game_started
    global players # players辞書もリセットまたはクリアしたい場合
    game_started = False
    
    # プレイヤー情報を完全にクリアするか、IDを保持してポジションなどをリセットするかは要検討
    # ここでは、ゲーム終了後にプレイヤーをロビーに戻す想定で、
    # 各プレイヤーのポジションと役割をリセットし、ゲーム開始待ち状態に戻します。
    for pid in players:
        players[pid]["pos"] = [0, 0] # 初期位置にリセット (または適当な待機位置)
        players[pid]["role"] = None # 役割をリセット

    print("[サーバー] ゲーム状態をリセットしました。新しいゲームの開始を待機します。")

# send_game_result の最後に呼び出す
def send_game_result(winner):
    global game_started
    result_msg = {
        "type": "game_result",
        "winner": winner
    }
    print("[送信] 勝敗結果を全員に送信:", winner)
    for p in players.values():
        try:
            server_socket.sendto(json.dumps(result_msg).encode(), p["addr"])
        except Exception as e:
            print(f"[送信エラー] {p['id']}: {e}")
    game_started = False  # ゲーム終了
    print(f"[🏁ゲーム終了] 勝者: {winner}")
    reset_server_game() # ★ ここでサーバーのゲーム状態をリセット
    
# 🔄 受信ループ開始
receive_loop()
