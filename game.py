import json
import random
import uuid

class Player():
    def __init__(self, nick:str, x:int, y:int, websocket):
        self.nick = nick
        self.x = x
        self.y = y
        self.websocket = websocket
        self.bombs_amount = 3
        self.bombs = [Bomb() for _ in range(self.bombs_amount)]
        self.score = 0

    def set_player_pos(self, x:int, y:int, walls):
        if [x, y] not in walls:
            self.x = x
            self.y = y

    def decrease_bombs(self):
        if self.bombs:
            return self.bombs.pop()

    def increase_bombs(self):
        self.bombs.append(Bomb())

    def get_pos(self):
        return (self.x, self.y)

    def pos_msg(self):
        pos_message = {
            "message_code": "player_pos",
            "nick": self.nick,
            "x": self.x,
            "y": self.y
        }

        return json.dumps(pos_message)

    def bomb_planted_msg(self):
        bomb = self.decrease_bombs()
        bomb.set_bomb_pos(self.x, self.y)
        bomb_message = {
            "message_code": "Bomb has been planted",
            "x": self.x,
            "y": self.y,
            "bomb_uid": str(bomb.bomb_uid) 
        }

        return json.dumps(bomb_message), bomb

    def bomb_amount_msg(self):
        bomb_amount_message = {
            "message_code": "bomb_amount",
            "amount": self.bombs_amount
        }

        return json.dumps(bomb_amount_message)

class Box():
    def __init__(self, x:int, y:int):
        self.uid = str(uuid.uuid4())
        self.pos = [x, y]

class Gift():
    def __init__(self, x:int, y:int, gift_type:str):
        self.uid = str(uuid.uuid4())
        self.type = gift_type
        self.pos = [x, y]

class Bomb():
    def __init__(self, x:int=None, y:int=None):
        self.uid = str(uuid.uuid4)
        self.range_x = 3
        self.range_y = 3

        if (x and y) != None:
            self.pos = [x, y]

    def set_bomb_pos(self, x:int=None, y:int=None):
        self.pos = [x, y]

class Game():
    def __init__(self, map_size_x:int, map_size_y:int, box_number:int, gift_number:int):
        self.map_size_x = map_size_x
        self.map_size_y = map_size_y
        self.box_number = box_number
        self.gift_number = gift_number
        self.possible_player_pos = [[map_size_x/2, 0], [0, map_size_y/2], [map_size_x, map_size_y/2], [map_size_x/2, map_size_y]]
        self.walls = self.generate_walls()
        self.boxes = self.generate_boxes()
        self.gifts = self.generate_gifts()
        self.default_bombs_num = 3
        # self.game_bombs = []
        self.players = dict()

    def add_player(self, client_uid, nick:str, websocket):
        self.players[client_uid] = Player(nick, *self.possible_player_pos.pop(), websocket)

    def handle_explosion(self, bomb, player_uid):
        objects_hit = []
        positions_hit = []

        blast = {
            "up": [[bomb.x, bomb.y + i] for i in range(1, bomb.bomb_range_y + 1)],
            "down": [[bomb.x, bomb.y + i] for i in range(-1, -bomb.bomb_range_y - 1, -1)],
            "right": [[bomb.x + i, bomb.y] for i in range(1, bomb.bomb_range_x + 1)],
            "left": [[bomb.x + i, bomb.y] for i in range(-1, -bomb.bomb_range_x - 1, -1)]
        }

        for direction in blast.values():
            for pos in direction:
                if pos in self.walls:
                    break
                else:
                    positions_hit.append(pos)

        for pos in positions_hit:
            for box in self.boxes:
                if pos == box.pos:
                    objects_hit.append(box)
                    self.players[player_uid].score += 1

            for player in self.players.values():
                if pos == player.pos:
                    objects_hit.append(player)
                    if self.players[player_uid] != player:
                        self.players[player_uid].score += 10

        explosion_message = {
            "msg_code": "Bomb exploded",
            "x_range": bomb.range_x,
            "y_range": bomb.range_y,
            "bomb_uid": str(bomb.uid),
            "objects_hit": json.dumps(objects_hit, default=self.obj_dict)
        }

        return json.dumps(explosion_message)

    def generate_boxes(self):
        boxes = []
        for _ in range(self.box_number):
            while True:
                if (pos := [random.randrange(0, self.map_size_x), random.randrange(0, self.map_size_y)]) not in (self.possible_player_pos and self.walls):
                    boxes.append(Box(*pos))
                    break

        return boxes

    # Dunno if gifts can only be placed where boxes are, or wherever
    # Gifts spawn at box pos !!!
    def generate_gifts(self):
        gifts = []
        gift_types = ["type1", "type2", "type3"]
        temp_boxes = self.boxes
        for _ in range(self.gift_number):
            box = random.choice(self.boxes)
            temp_boxes.remove(box)
            gifts.append(Gift(*box.pos, random.choice(gift_types)))

        return gifts

    def generate_walls(self):
        walls = []
        for i in range(self.map_size_x):
            walls.append([i, 0])
            walls.append([i, self.map_size_y-1])

        for i in range(1, self.map_size_y):
            walls.append([0, i])
            walls.append([self.map_size_x-1, i])

        for i in range(int((self.map_size_x-2)/2)+1):
            for j in range(int((self.map_size_y-2)/2)+1):
                walls.append([i*2, j*2])

        return walls

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
            "box": json.dumps(self.boxes, default=self.obj_dict),
            "gifts": json.dumps(self.gifts, default=self.obj_dict)
        }
        
        return json.dumps(welcome_message)

    # When player disconnects set his current pos to -1, -1 
    def disconnect_player(self, uid):
        disconnect_message = {
            "message_code": "player_pos",
            "nick": self.players[uid].nick,
            "x": -1,
            "y": -1
        }

        self.players.pop(uid)

        return json.dumps(disconnect_message)
