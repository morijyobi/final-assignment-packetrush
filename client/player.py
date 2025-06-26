# player.py
#プレイヤーの動きと表示を管理
import pygame as pg, sys
import uuid
import random
from utils import config
# プレイヤーの画像
class Player:
    charaimg1 = pg.image.load("client/assets/images/player1.png")
    charaimg1 = pg.transform.scale(charaimg1, (50, 50))
    chararect1 = pg.Rect(0, 0, 50, 50)
    charaimg2 = pg.image.load("client/assets/images/player2.png")
    charaimg2 = pg.transform.scale(charaimg2, (50, 50))
    chararect2 = pg.Rect(800, 0, 50, 50)
    charaimg3 = pg.image.load("client/assets/images/player3.png")
    charaimg3 = pg.transform.scale(charaimg3, (50, 50))
    chararect3 = pg.Rect(0, 600, 50, 50)
    charaimg4 = pg.image.load("client/assets/images/player4.png")
    charaimg4 = pg.transform.scale(charaimg4, (50, 50))
    chararect4 = pg.Rect(800, 600, 50, 50)
    oni = pg.image.load("client/assets/images/oni.png")
    oni = pg.transform.scale(oni, (50, 50))
    onirect = pg.Rect(400, 300, 50, 50)
    # 速度
    player_speed = 5
    oni_speed = 6