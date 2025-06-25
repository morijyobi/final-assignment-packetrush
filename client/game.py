#ソケットの通信の準備、プレイヤー情報の送受信など
import pygame as pg, sys
import socket
import json
from player import Player
from utils import config
pg.init()
screen = pg.display.set_mode((800, 600))
# 背景画像
haikeimg = pg.image.load("client/assets/images/map.png")
haikeimg = pg.transform.scale(haikeimg, (800, 600))
class Game:
    def __init__(self):
        # 障害物画像を種類ごとに辞書で読み込み
        self.obstacle_images = {
            "momiji" : pg.transform.scale(pg.image.load("client/assets/images/momiji.png"), (60, 60)), 
            "ido" : pg.transform.scale(pg.image.load("client/assets/images/ido_gray.png"), (30, 30)),
            "iwa" : pg.transform.scale(pg.image.load("client/assets/images/iwa_01.png"), (30, 30)),
            "otera" : pg.transform.scale(pg.image.load("client/assets/images/otera.png"), (80, 80)),
            "torii" : pg.transform.scale(pg.image.load("client/assets/images/torii01.png"), (80, 80))
            }
        # 障害物データ(種類と位置の組)
        self.obstacles = [
            {"type" : "momiji", "pos" : (230, 180)},
            {"type" : "momiji", "pos" : (230, 260)},
            {"type" : "momiji", "pos" : (230, 340)},
            {"type" : "otera", "pos" : (380, 50)},
            {"type" : "torii", "pos" : (383, 130)},
            {"type" : "iwa", "pos" : (350, 250)},
            {"type" : "iwa", "pos" : (450, 330)},
            {"type" : "ido", "pos" : (500, 90)},
            {"type" : "momiji", "pos" : (530, 180)},
            {"type" : "momiji", "pos" : (530, 260)},
            {"type" : "momiji", "pos" : (530, 340)}
        ]
        # 将来、ここでプレイヤーなども初期化
    def draw(self):
        # 背景を描画
        screen.blit(haikeimg, (0, 0))
        # 障害物の描画
        for obs in self.obstacles:
            img = self.obstacle_images.get(obs["type"])
            if img:
                screen.blit(img, obs["pos"])
        pg.display.flip()
        
    def run(self):
        while True:
            self.draw()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
        
if __name__ == "__main__":
    game = Game()
    game.run()