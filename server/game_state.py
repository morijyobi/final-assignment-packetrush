#プレイヤー情報を格納、ゲームの進行状況(例:待機中、プレイ中、終了など)の管理、タイマー処理、プレイヤーの追加・削除、位置更新など
import random
from server.player_state import PlayerState
class GameState:
    def __init__(self):
        # プレイヤーの一覧。keyはプレイヤーID（例えば接続元のアドレスなど）、valueはPlayerStateインスタンス
        self.players = {}
        self.tagged_player_id = None # 鬼のIDを保持(1人だけ)
    def add_player(self, player_id, initial_position=(100, 100)):
        if player_id in self.players:
            print(f"プレイヤー{player_id}はすでに参加しています。")
            return
        player = PlayerState(player_id, initial_position)
        print(f"プレイヤーID{player_id}が参加しました。")
        self.players[player_id] = player
    def remove_player(self, player_id):
        if player_id in self.players:
            del self.players[player_id]
            print(f"プレイヤーID{player_id}が退出しました。")
            if self.tagged_player_id == player_id:
                self.tagged_player_id = None # 鬼が抜けたらリセット