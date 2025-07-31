import pygame as pg
import os
import sys
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
class Item:
    def __init__(self, image_path, pos, item_type="speed"):
        image_path = resource_path(image_path)
        try:
            self.image = pg.image.load(image_path).convert_alpha()
            self.image = pg.transform.scale(self.image, (40, 40))
        except Exception as e:
            print(f"[画像読み込みエラー]{image_path}を読み込めませんでした:{e}")
            # フォールバックで赤い四角を表示
            self.image = pg.Surface((40, 40))
            self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(topleft=pos)
        self.pos = pos
        self.type = item_type
        self.active = True # 表示中かどうか
    def draw(self, screen):
        if self.active:
            screen.blit(self.image, self.rect)
    def check_collision(self, player_rect):
        """プレイヤーと接触したら取得済みに"""
        if self.active and self.rect.colliderect(player_rect):
            self.active = False
            return True
        return False