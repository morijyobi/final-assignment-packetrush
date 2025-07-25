# player.py
# プレイヤーの動きと表示を管理
import pygame as pg
import sys
import os
import random
class Player:
    player_speed = 5
    oni_speed = 6
    p_image = 0
    image_list = ["client/assets/images/player1.png", "client/assets/images/player2.png", "client/assets/images/player3.png", "client/assets/images/player4.png"]
    def __init__(self, role="runner", x=100, y=100, name=""):
        self.role = role
        self.name = name
        self.x, self.y = x, y
        # デプロイ時にパスのエラーを解消するために使った関数
        def resource_path(relative_path):
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)

        if role == "oni":
            charimage_path = resource_path("client/assets/images/oni.png")
            self.oni_image = pg.image.load(charimage_path)
            self.oni_image = pg.transform.scale(self.oni_image, (40, 40))
            self.onirect = self.oni_image.get_rect(topleft=(x, y))
        else:
            charimage_path = resource_path(Player.image_list[self.p_image])
            self.player_image = pg.image.load(charimage_path)
            self.player_image = pg.transform.scale(self.player_image, (40, 40))
            self.chararect1 = self.player_image.get_rect(center=(x + 20, y + 20)).inflate(-10, -10) # 当たり判定を縮小
            Player.p_image = (Player.p_image + 1) % len(Player.image_list)