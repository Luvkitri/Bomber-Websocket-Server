import json
import random

class Player():
    def __init__(self, nick:str, x:int, y:int):
        self.nick = nick
        self.x = x
        self.y = y

    def set_player_pos(self, x:int, y:int):
        self.x = x
        self.y = y

    def get_pos(self):
        pos_message = {
            "message_code": "player_pos",
            "nick": self.nick,
            "x": self.x,
            "y": self.y
        }

        return json.dumps(pos_message)

class Game():
    def __init__(self, map_size_x:int, map_size_y:int, box_number:int, gift_number:int):
        self.map_size_x = map_size_x
        self.map_size_y = map_size_y
        self.box_number = box_number
        self.gift_number = gift_number
        self.possible_player_pos = [(map_size_x/2, 0), (0, map_size_y/2), (map_size_x, map_size_y/2), (map_size_x/2, map_size_y)]
        self.box = self.generate_boxes()

    def generate_boxes(self):
        boxes = []
        for _ in range(self.box_number):
            while True:
                if pos := (random.randrange(0, self.map_size_x), random.randrange(0, self.map_size_y)) not in self.possible_player_pos:
                    boxes.append(list(pos))
                    break

        return boxes


    def create_welcome_msg(self, nick:str, uid, bombs_amount:int):
        welcome_message = {
            "msg_code": "welcome_msg",
            "map_size_x": self.map_size_x,
            "map_size_y": self.map_size_y,
            "client_uid": uid,
            "bombs_amount": bombs_amount,
            "current_score": 0,
            "box": self.box
        }

