import socket
import json
import uuid
import threading
import time
import pygame as pg
# サーバーソケット初期化
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(("0.0.0.0", 5000))
server_socket.settimeout(0.5)

players = {}
REQUIRED_PLAYERS = 4
game_started = False
print("サーバー起動: 0.0.0.0:5000 で待機中...")
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
        except socket.timeout:
            continue
        except Exception as e:
            print(f"[受信エラー] {e}")

# ✅ 個別のクライアントメッセージ処理
def process_message(message, addr):
    global game_started
    msg_type = message.get("type")
    
    if msg_type == "connect_request":
        player_id = str(uuid.uuid4())
        name = message.get("name", "Player")
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
                    "role": p["role"]
                } for pid, p in players.items()
            }
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
            print(f"[更新] {player_id} の位置を {new_pos} に更新")

            # 👇 鬼がランナーに接触しているかをチェック（ゲーム開始後のみ）
            if game_started:
                oni_pos = None
                for pid, p in players.items():
                    if p["role"] == "oni":
                        oni_pos = p["pos"]
                        break
                if oni_pos:
                    for pid, p in players.items():
                        if p["role"] == "runner":
                            runner_pos = p["pos"]
                            # 20px以内なら接触とみなす（大きさに合わせて調整）
                            if abs(oni_pos[0] - runner_pos[0]) < 30 and abs(oni_pos[1] - runner_pos[1]) < 30:
                                print(f"[👹接触] 鬼がランナーを捕まえました！")
                                send_game_result("oni")
                                break
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

    else:
        print(f"[警告] サーバーから未知の応答: {message}")
# プレイヤーの役割の割り振り
def assign_roles():
    player_ids = list(players.keys())
    oni_id = player_ids[0]  # 先頭を鬼にする（適宜ランダムでも可）

    for pid in player_ids:
        if pid == oni_id:
            players[pid]["role"] = "oni"
        else:
            players[pid]["role"] = "runner"
# ゲーム開始
def start_game():
    global game_started
    game_started = True
    assign_initial_positions()  # ここで初期位置を決める
    for pid in players:
        addr = players[pid].get("addr")  # addr を保存していない場合は対応が必要
        if addr:
            start_msg = {"type": "start_game"}
            server_socket.sendto(json.dumps(start_msg).encode(), addr)
    print("✅ プレイヤーが揃いました。ゲームを開始します。")
    
def send_game_result(winner):
    global game_started
    result_msg = {
        "type": "game_result",
        "winner": winner
    }
    for p in players.values():
        try:
            server_socket.sendto(json.dumps(result_msg).encode(), p["addr"])
        except Exception as e:
            print(f"[送信エラー] {p['id']}: {e}")
    game_started = False  # ゲーム終了
    print(f"[🏁ゲーム終了] 勝者: {winner}")
    
# 🔄 受信ループ開始
receive_loop()
