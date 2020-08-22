class Player():
    def __init__(self, nick:str, x:int, y:int):
        self.nick = nick
        self.x = x
        self.y = y

    def set_player_pos(self, x:int, y:int):
        self.x = x
        self.y = y
