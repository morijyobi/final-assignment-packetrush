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
    def draw(self):
        screen.blit(haikeimg, (0, 0))
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