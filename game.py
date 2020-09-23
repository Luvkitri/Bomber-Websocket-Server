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
        self.dead = False

    def set_player_pos(self, x:int, y:int, walls, boxes, gifts):
        if not self.dead:
            flag = True
            for box in boxes:
                if [x, y] == box.pos:
                    flag = False
                    break
            
            if [x, y] not in walls and flag:
                self.x = x
                self.y = y

            for gift in gifts:
                if [x, y] == gift.pos:
                    gifts.remove(gift)
                    return self.gift_picked_msg(gift.uid)

        return None

    def set_player_pos_dead(self, x:int, y:int):
        self.x = x
        self.y = y

    def decrease_bombs(self):
        if self.bombs:
            return self.bombs.pop()

        return "No more bombs!"

    def increase_bombs(self):
        if self.bombs_amount > len(self.bombs):
            self.bombs.append(Bomb())

    def get_pos(self):
        return (self.x, self.y)

    def pos_msg(self):
        pos_message = {
            "msg_code": "player_pos",
            "nick": self.nick,
            "x": self.x,
            "y": self.y
        }

        return json.dumps(pos_message)

    def bomb_planted_msg(self, bomb):
        bomb.set_bomb_pos(self.x, self.y)
        bomb_message = {
            "msg_code": "Bomb has been planted",
            "x": self.x,
            "y": self.y,
            "bomb_uid": bomb.uid 
        }

        print(bomb)

        return json.dumps(bomb_message)

    def bomb_amount_msg(self):
        bomb_amount_message = {
            "msg_code": "bomb_amount",
            "amount": len(self.bombs)
        }

        return json.dumps(bomb_amount_message)

    def current_score_msg(self):
        current_score_message = {
            "msg_code": "current score",
            "score": self.score
        }

        return json.dumps(current_score_message)

    def gift_picked_msg(self, gift_uid):
        gift_picked_message = {
            "msg_code": "gift_picked",
            "gift_uid": gift_uid
        }

        return json.dumps(gift_picked_message)

    def asdict(self):
        return { 'nick': self.nick, 'x': self.x, 'y': self.y }

    def __str__(self):
        return "PLAYER => |NICK: " + self.nick + "| |POS: (" + str(self.x) + ", " + str(self.y) + ")| |SCORE: " + str(self.score) + "|"

class Box():
    def __init__(self, x:int, y:int):
        self.uid = str(uuid.uuid4())
        self.pos = [x, y]

    def asdict(self):
        return { 'uid': self.uid, 'pos': self.pos }

class Gift():
    def __init__(self, x:int, y:int, gift_type:str):
        self.uid = str(uuid.uuid4())
        self.type = gift_type
        self.pos = [x, y]

    def asdict(self):
        return { 'uid': self.uid, 'type': self.type,'pos': self.pos }

class Bomb():
    def __init__(self, x:int=None, y:int=None):
        self.uid = str(uuid.uuid4())
        self.range_x = 3
        self.range_y = 3

        if (x and y) != None:
            self.pos = [x, y]

    def set_bomb_pos(self, x:int=None, y:int=None):
        self.pos = [x, y]

    def asdict(self):
        return { 'uid': self.uid, 'range_x': self.range_x,'range_y': self.range_y }

    def __str__(self):
        return "BOMB => |UID: {0}| |POS: ({1}, {2})| |X_RANGE: {3}| |Y_RANGE: {4}|".format(self.uid, self.pos[0], self.pos[1], self.range_x, self.range_y)

class Game():
    def __init__(self, map_size_x:int, map_size_y:int, box_number:int, gift_number:int):
        self.map_size_x = map_size_x
        self.map_size_y = map_size_y
        self.box_number = box_number
        self.gift_number = gift_number
        self.possible_player_pos = [[1, 1], [1, map_size_y-2], [map_size_x-2, 1], [map_size_x-2, map_size_y-2]]
        self.no_box_pos = [[1, 2], [2, 1], [1, map_size_y-3], [2, map_size_y-2], [map_size_x-3, 1],
                            [map_size_x-2, 2], [map_size_x-3, map_size_y-2], [map_size_x-2, map_size_y-3]]
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
            "up": [[bomb.pos[0], bomb.pos[1] + i] for i in range(1, bomb.range_y + 1)],
            "down": [[bomb.pos[0], bomb.pos[1] + i] for i in range(-1, -bomb.range_y - 1, -1)],
            "right": [[bomb.pos[0] + i, bomb.pos[1]] for i in range(1, bomb.range_x + 1)],
            "left": [[bomb.pos[0] + i, bomb.pos[1]] for i in range(-1, -bomb.range_x - 1, -1)]
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
                    self.boxes.remove(box)
                    objects_hit.append(box.uid)
                    self.players[player_uid].score += 1

            for alive_player in [player for player in self.players.values() if not player.dead]:
                if pos == [alive_player.x, alive_player.y]:
                    objects_hit.append(alive_player.nick)
                    alive_player.dead = True
                    if self.players[player_uid] != alive_player:
                        self.players[player_uid].score += 10
                        
        explosion_message = {
            "msg_code": "Bomb exploded",
            "x_range": bomb.range_x,
            "y_range": bomb.range_y,
            "bomb_uid": bomb.uid,
            "objects_hit": objects_hit
        }

        return json.dumps(explosion_message)

    def generate_boxes(self):
        boxes = []
        boxes_pos = []
        for _ in range(self.box_number):
            while True:
                if (pos := [random.randrange(0, self.map_size_x), random.randrange(0, self.map_size_y)]) not in self.possible_player_pos + self.walls + boxes_pos + self.no_box_pos:
                    boxes_pos.append(pos)
                    boxes.append(Box(*pos))
                    break

        return boxes

    def generate_gifts(self):
        gifts = []
        gift_types = ["bomb"]
        temp_boxes = self.boxes.copy()
        for _ in range(self.gift_number):
            box = random.choice(temp_boxes)
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
        box_list = []
        gift_list = []
        for box, gift in zip(self.boxes, self.gifts):
            box_list.append(box.asdict())
            gift_list.append(gift.asdict())

        welcome_message = {
            "msg_code": "welcome_msg",
            "map_size_x": self.map_size_x,
            "map_size_y": self.map_size_y,
            "client_uid": uid,
            "bombs_amount": bombs_amount,
            "current_score": 0,
            "box": box_list,
            "gifts": gift_list
        }

        return json.dumps(welcome_message)    
