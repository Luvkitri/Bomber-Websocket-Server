import json
import random
import uuid

class Player():
    def __init__(self, nick:str, x:int, y:int, websocket):
        self.nick = nick
        self.x = x
        self.y = y
        self.websocket = websocket

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

    def bomb_planted_msg(self):
        bomb_uid = uuid.uuid4()
        bomb_message = {
            "message_code": "Bomb has been planted",
            "x": self.x,
            "y": self.y,
            "bomb_uid": str(bomb_uid) 
        }

        return json.dumps(bomb_message), bomb_uid 
class Box():
    def __init__(self, x:int, y:int):
        self.box_uid = str(uuid.uuid4())
        self.box_pos = [x, y]

class Gift():
    def __init__(self, x:int, y:int, gift_type:str):
        self.gift_uid = str(uuid.uuid4())
        self.gift_type = gift_type
        self.gift_pos = [x, y]

class Bomb():
    def __init__(self, x:int, y:int):
        self.bomb_uid = str(uuid.uuid4)
        self.bomb_pos = [x, y]
        self.bomb_range_x = 6
        self.bomb_range_y = 6

class Game():
    def __init__(self, map_size_x:int, map_size_y:int, box_number:int, gift_number:int):
        self.map_size_x = map_size_x
        self.map_size_y = map_size_y
        self.box_number = box_number
        self.gift_number = gift_number
        self.possible_player_pos = [(map_size_x/2, 0), (0, map_size_y/2), (map_size_x, map_size_y/2), (map_size_x/2, map_size_y)]
        self.box = self.generate_boxes()
        self.gifts = self.generate_gifts()
        self.default_bombs_num = 3

    def generate_boxes(self):
        boxes = []
        for _ in range(self.box_number):
            while True:
                if (pos := (random.randrange(0, self.map_size_x), random.randrange(0, self.map_size_y))) not in self.possible_player_pos:
                    boxes.append(Box(*pos))
                    break

        return boxes

    # Dunno if gifts can only be placed where boxes are, or wherever
    def generate_gifts(self):
        gifts = []
        gift_types = ["type1", "type2", "type3"]
        for _ in range(self.gift_number):
            while True:
                if (pos := (random.randrange(0, self.map_size_x), random.randrange(0, self.map_size_y))) not in self.possible_player_pos:
                    gifts.append(Gift(*pos, random.choice(gift_types)))
                    break

        return gifts

    def obj_dict(self, obj):
        return obj.__dict__

    def create_welcome_msg(self, nick:str, uid, bombs_amount:int):
        welcome_message = {
            "msg_code": "welcome_msg",
            "map_size_x": self.map_size_x,
            "map_size_y": self.map_size_y,
            "client_uid": str(uid),
            "bombs_amount": bombs_amount,
            "current_score": 0,
            "box": json.dumps(self.box, default=self.obj_dict),
            "gifts": json.dumps(self.gifts, default=self.obj_dict)
        }
        
        return json.dumps(welcome_message)

