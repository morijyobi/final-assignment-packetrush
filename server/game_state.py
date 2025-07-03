#プレイヤー情報を格納、ゲームの進行状況(例:待機中、プレイ中、終了など)の管理、タイマー処理、プレイヤーの追加・削除、位置更新など
import random
from server.player_state import PlayerState
# プレイヤー情報と役割割当、ゲーム進行状況の管理

import random
from server.player_state import PlayerState
import pygame as pg
from client.player import Player

class GameState:
    def __init__(self):
        self.players = {}  # {player_id: PlayerState}
        self.tagged_player_id = None  # 鬼のID

        # 役割ごとの初期位置
        self.start_positions = {
            "oni": (50, 50),  # 左上
            "runner": [
                (50, 500),    # 左下
                (700, 50),    # 右上
                (700, 500)    # 右下
            ],
            "spectator": (400, 300)  # 中央
        }
        # 障害物の矩形(座標とサイズ)
        self.obstacles = [
            pg.Rect(230, 180, 60, 60),
            pg.Rect(230, 260, 60, 60),
            pg.Rect(230, 340, 60, 60),
            pg.Rect(380, 50, 80, 80),
            pg.Rect(383, 130, 80, 80),
            pg.Rect(350, 250, 30, 30),
            pg.Rect(450, 330, 30, 30),
            pg.Rect(500, 90, 30, 30),
            pg.Rect(530, 180, 60, 60),
            pg.Rect(530, 260, 60, 60),
            pg.Rect(530, 340, 60, 60)
            ]
    def add_player(self, player_id):
        if player_id in self.players:
            print(f"⚠️ 既に参加済: {player_id}")
            return

        # 仮の位置で初期化（役割割当後に更新）
        self.players[player_id] = PlayerState(player_id)
        print(f"✅ プレイヤー参加: {player_id}")

    def remove_player(self, player_id):
        if player_id in self.players:
            print(f"❌ プレイヤー退出: {player_id}")
            if self.tagged_player_id == player_id:
                self.tagged_player_id = None
            del self.players[player_id]

    def assign_roles(self, max_runners=3):
        """鬼1人、最大3人を逃げ、残りを観戦に割り当てる"""
        player_ids = list(self.players.keys())
        random.shuffle(player_ids)

        if not player_ids:
            print("⚠️ プレイヤーがいません。")
            return

        # 鬼を1人選ぶ
        self.tagged_player_id = player_ids[0]
        self.players[self.tagged_player_id].role = "oni"
        self.players[self.tagged_player_id].position = self.start_positions["oni"]
        print(f"🎯 鬼に選ばれたプレイヤー: {self.tagged_player_id}")

        # 逃げ役の割り当て
        runner_ids = player_ids[1:1 + max_runners]
        available_positions = self.start_positions["runner"][:]

        for pid in runner_ids:
            self.players[pid].role = "runner"
            if available_positions:
                pos = available_positions.pop(0)
            else:
                pos = (400, 500)  # 予備位置
            self.players[pid].position = pos

        # 残りは観戦者
        for pid in player_ids[1 + max_runners:]:
            self.players[pid].role = "spectator"
            self.players[pid].position = self.start_positions["spectator"]

    def get_game_state(self):
        """全プレイヤーの状態を辞書で返す（クライアント送信用）"""
        return {
            pid: player.to_dict()
            for pid, player in self.players.items()
        }

    def collision_process(self):
        #　鬼と逃げる人の衝突処理
        oni = self.players.get(self.tagged_player_id)
        if not oni:
            return
        oni_rect = pg.Rect(oni.position[0], oni.position[1], 50, 50)
        for pid, player in self.players.items():
            if player.role == "runner":
                runner_rect = pg.Rect(player.position[0], player.position[1], 50, 50)
                if oni_rect.colliderect(runner_rect):
                    print(f"{pid}が鬼に捕まりました!")
    def update_player_position(self, player_id, new_pos):
        if player_id not in self.players:
            return
        player = self.players[player_id]
        new_rect = pg.Rect(new_pos[0], new_pos[1], 50, 50)
        # 障害物とぶつかるなら移動しない
        for obstacle in self.obstacles:
            if new_rect.collidedict(obstacle):
                print(f"{player_id}は障害物にぶつかりました")
                return # 移動せず終了
        # 障害物が無ければ位置を更新
        player.position = new_pos
            