#プレイヤーの動きと表示を管理
import pygame as pg, sys
import uuid
import random
from utils import config
# プレイヤーの画像
charaimg1 = pg.image.load("client/assets/images/dotpict_20250616_093204 (1).png")
charaimg1 = pg.transform.scale(charaimg1, (50, 50))
chararect1 = pg.Rect(0, 0, 50, 50)
charaimg2 = pg.image.load("client/assets/images/dotpict_20250616_093225 (1).png")
charaimg2 = pg.transform.scale(charaimg2, (50, 50))
chararect2 = pg.Rect(0, 0, 50, 50)
charaimg3 = pg.image.load("client/assets/images/dotpict_20250616_093227 (1).png")
charaimg3 = pg.transform.scale(charaimg3, (50, 50))
chararect3 = pg.Rect(0, 0, 50, 50)
charaimg4 = pg.image.load("client/assets/images/dotpict_20250616_093230 (1).png")
charaimg4 = pg.transform.scale(charaimg4, (50, 50))
chararect4 = pg.Rect(0, 0, 50, 50)
oni = pg.image.load("client/assets/images/dotpict_20250616_093054 (1).png")
oni = pg.transform.scale(oni, (50, 50))
onirect = pg.Rect(0, 0, 50, 50)
class Player:
    pass