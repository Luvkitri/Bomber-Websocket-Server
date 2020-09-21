import asyncio
import websockets
import json
import uuid
import threading
from game import Player, Game

# PLAYERS = dict()

# https://stackoverflow.com/questions/45419723/python-timer-with-asyncio-coroutine
class Timer:
    def __init__(self, timeout, callback, *args):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job(args))

    async def _job(self, args):
        await asyncio.sleep(self._timeout)
        await self._callback(*args)

    def cancel(self):
        self._task.cancel()

class Server():
    def __init__(self):
        self.game = self.create_game()

    async def on_connect(self, data, websocket):
        if len(self.game.players) < 4:
            # Register player
            client_uid = str(uuid.uuid4())
            self.game.add_player(client_uid, data['nick'], websocket)
            print(data['nick'])
            print(self.game.players[client_uid])

            # Welcome message is sent here
            await websocket.send(self.game.create_welcome_msg(data['nick'], client_uid, self.game.default_bombs_num))

            # Send starting position to each player            
            await self.notify_players(self.game.players[client_uid].pos_msg())
        else:
            print("Session is full")

    async def on_move(self, data):
        gift_picked_message = self.game.players[data['uid']].set_player_pos(data['x'], data['y'], self.game.walls, self.game.boxes, self.game.gifts)

        if gift_picked_message != None:
            await self.game.players[data['uid']].websocket.send(gift_picked_message)
            self.game.players[data['uid']].bombs_amount += 1
            self.game.players[data['uid']].increase_bombs()
            await self.game.players[data['uid']].websocket.send(self.game.players[data['uid']].bomb_amount_msg())


        await self.notify_players(self.game.players[data['uid']].pos_msg())
        print(f"Player {data['uid']} has moved to {data['x']}, {data['y']}")

    async def on_bomb(self, data):
        # Remove one bomb from player
        bomb = self.game.players[data['uid']].decrease_bombs()

        # Send current amount of bombs to a player
        await self.game.players[data['uid']].websocket.send(self.game.players[data['uid']].bomb_amount_msg())
        
        # Inform players about planted bomb
        if isinstance(bomb, str):
            await self.game.players[data['uid']].websocket.send(bomb)
            return

        bomb_msg = self.game.players[data['uid']].bomb_planted_msg(bomb)
        await self.notify_players(bomb_msg)
        print(f"Player {self.game.players[data['uid']].nick} has planted a bomb at {self.game.players[data['uid']].get_pos()}")

        # Set a bomb timer
        bomb_timer = Timer(3, self.bomb_exploded, bomb, data['uid'])

        # Set a bomb refresher timer
        refresh_timer = Timer(6, self.bomb_refreshed, self.game.players[data['uid']])

    async def on_disconnect(self, data):
        await self.game.players[data['uid']].websocket.close()
        self.game.players.pop(data['uid'])
    
    async def bomb_exploded(self, bomb, player_uid):
        message, players_hit = self.game.handle_explosion(bomb, player_uid)
        print(f'Bomb {bomb.uid} has exploded')

        if players_hit:
            for player_uid in players_hit:
                self.game.players[player_uid].set_player_pos_dead(1000, 1000)
                await self.notify_players(self.game.players[player_uid].pos_msg())

        await self.notify_players(message)
        
        # Send score to a player
        await self.game.players[player_uid].websocket.send(self.game.players[player_uid].current_score_msg())

    async def bomb_refreshed(self, player):
        player.increase_bombs()
        print("Bomb refreshed")
        await player.websocket.send(player.bomb_amount_msg())

    async def notify_players(self, message):
        if self.game.players:
            await asyncio.wait([player.websocket.send(message) for player in self.game.players.values()])

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
                print(f"Number of players: {len(self.game.players)}")
            elif data['msg_code'] == 'player_move':
                # Handle player movement
                await self.on_move(data)
            elif data['msg_code'] == 'player_plant_bomb':
                # Plant a bomb on map
                await self.on_bomb(data)
            elif data['msg_code'] == 'disconnect':
                # Remove player
                await self.on_disconnect(data)
            else:
                print("Unknown message.")

        

server = Server()
start_server = websockets.serve(server.server, "localhost", 5000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()