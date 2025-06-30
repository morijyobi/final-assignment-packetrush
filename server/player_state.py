#各プレイヤーの状態（位置・鬼かどうかなど）の管理
class PlayerState:
    def __init__(self, player_id, position=(0, 0)):
        self.player_id = player_id
        self.position = position
        self.is_it = False # 鬼かどうか
    def to_dict(self):
        return {
            "id": self.player_id,
            "position": self.position,
            "role": self.role  
    }

        