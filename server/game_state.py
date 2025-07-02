#プレイヤー情報を格納、ゲームの進行状況(例:待機中、プレイ中、終了など)の管理、タイマー処理、プレイヤーの追加・削除、位置更新など
import random
from server.player_state import PlayerState
# プレイヤー情報と役割割当、ゲーム進行状況の管理


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

    def update_player_position(self, player_id, new_pos):
        if player_id in self.players:
            self.players[player_id].position = new_pos

    def get_game_state(self):
        """全プレイヤーの状態を辞書で返す（クライアント送信用）"""
        return {
            pid: player.to_dict()
            for pid, player in self.players.items()
        }
