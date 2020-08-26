import asyncio
import websockets
import json
import uuid
from game import Player, Game

PLAYERS = dict()


class Server():
    def __init__(self):
        self.game = self.create_game()

    async def on_connect(self, data, websocket):
        if len(PLAYERS) < 4:
            # Register player
            client_uid = uuid.uuid4()
            PLAYERS[client_uid] = Player(data['nick'], *self.game.possible_player_pos.pop())

            # Send starting position to each player            
            await self.notify_players(PLAYERS[client_uid].get_pos())

            # Welcome message is sent here
            await websocket.send('welcome_message')
        else:
            print("Session is full")

    async def notify_players(self, message):
        if PLAYERS:
            await asyncio.wait([player.send(message) for player in PLAYERS])

    async def create_game(self):
        with open('json/config.json') as f:
            config = json.load(f)
        
        return Game(config['map_size_x'], config['map_size_y'], config['box_number'], config['gift_number'])
        

    async def server(self, websocket, path):
        async for message in websocket:
            data = json.loads(message)
            if data['msg_code'] == 'connect':
                # Add new player
                await self.on_connect(data, websocket)
                print(f'Number of players: {len(PLAYERS)}')
            elif data['msg_code'] == 'player_move':
                pass
            elif data['msg_code'] == 'player_plant_bomb':
                pass
            elif data['msg_code'] == 'disconnect':
                # Remove player
                pass
            else:
                print("Unknown message.")

        

server = Server()
start_server = websockets.serve(server, "localhost", 5000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()