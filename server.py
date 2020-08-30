import asyncio
import websockets
import json
import uuid
import threading
from game import Player, Game

PLAYERS = dict()

# https://stackoverflow.com/questions/45419723/python-timer-with-asyncio-coroutine
class Timer:
    def __init__(self, timeout, callback, *args):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job(args))

    async def _job(self, args):
        await asyncio.sleep(self._timeout)
        await self._callback(args)

    def cancel(self):
        self._task.cancel()

class Server():
    def __init__(self):
        self.game = self.create_game()

    async def on_connect(self, data, websocket):
        if len(PLAYERS) < 4:
            # Register player
            client_uid = uuid.uuid4()
            PLAYERS[client_uid] = Player(data['nick'], *self.game.possible_player_pos.pop(), websocket)

            # Send starting position to each player            
            await self.notify_players(PLAYERS[client_uid].pos_msg())

            # Welcome message is sent here
            await websocket.send(self.game.create_welcome_msg(data['nick'], client_uid, self.game.default_bombs_num))
        else:
            print("Session is full")

    async def on_move(self, data):
        PLAYERS[data['uid']].set_player_pos(data['x'], data['y'])
        await self.notify_players(PLAYERS[data['uid']].pos_msg())
        print(f"Player {data['uid']} has moved to {data['x']}, {data['y']}")

    async def on_bomb(self, data):
        # Decrease number of bombs player has
        PLAYERS[data['uid']].decrease_bombs()
    
        # Send current amount of bombs to a player
        PLAYERS[data['uid']].websocket.send(PLAYERS[data['uid']].bomb_amount_msg)

        # Inform players about planted bomb
        bomb_msg, bomb = PLAYERS[data['uid']].bomb_planted_msg()
        await self.notify_players(bomb_msg)
        print(f"Player {data['uid']} has planted a bomb at {PLAYERS[data['uid']].get_pos()}")

        # Set a bomb timer
        bomb_timer = Timer(3, self.bomb_exploded, (bomb, PLAYERS))

        # Set a bomb refresher timer
        refresh_timer = Timer(6, self.bomb_refreshed, PLAYERS[data['uid']])
        
    async def bomb_exploded(self, bomb, players):
        self.game.handle_explosion(bomb, players)

    async def bomb_refreshed(self, player):
        player.increase_bombs()

    async def notify_players(self, message):
        if PLAYERS:
            await asyncio.wait([player.websocket.send(message) for player in PLAYERS.values()])

    def create_game(self):
        with open('json/config.json') as f:
            config = json.load(f)
        
        return Game(config['map_size_x'], config['map_size_y'], config['box_number'], config['gift_number'])      

    async def server(self, websocket, path):
        async for message in websocket:
            data = json.loads(message)
            if data['msg_code'] == 'connect':
                # Add new player
                await self.on_connect(data, websocket)
                print(f"Number of players: {len(PLAYERS)}")
            elif data['msg_code'] == 'player_move':
                # Handle player movement
                await self.on_move(data)
            elif data['msg_code'] == 'player_plant_bomb':
                # Plant a bomb on map
                await self.on_bomb(data)
            elif data['msg_code'] == 'disconnect':
                # Remove player
                pass
            else:
                print("Unknown message.")

        

server = Server()
start_server = websockets.serve(server.server, "localhost", 5000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()