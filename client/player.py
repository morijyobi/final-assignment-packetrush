# player.py
#プレイヤーの動きと表示を管理
import pygame as pg, sys
import uuid
from client.utils import config
# プレイヤーの画像
class Player:
    # images = {
    #      "runner1":"client/assets/images/player1.png",
    #      "runner2":"client/assets/images/player2.png",
    #      "runner3":"client/assets/images/player3.png",
    #      "oni":"client/assets/images/oni.png"
    #  }
    # images_rect = (50, 50)
    charaimg1 = pg.image.load("client/assets/images/player1.png")
    charaimg1 = pg.transform.scale(charaimg1, (50, 50))
    chararect1 = pg.Rect(800, 0, 50, 50)
    charaimg2 = pg.image.load("client/assets/images/player2.png")
    charaimg2 = pg.transform.scale(charaimg2, (50, 50))
    chararect2 = pg.Rect(800, 600, 50, 50)
    charaimg3 = pg.image.load("client/assets/images/player3.png")
    charaimg3 = pg.transform.scale(charaimg3, (50, 50))
    chararect3 = pg.Rect(0, 600, 50, 50)
    oni = pg.image.load("client/assets/images/oni.png")
    oni = pg.transform.scale(oni, (50, 50))
    onirect = pg.Rect(0, 0, 50, 50)
    # 速度
    player_speed = 5
    oni_speed = 6