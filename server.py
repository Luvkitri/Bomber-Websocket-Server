import asyncio
import websockets
import json
import uuid
from game import Player

PLAYERS = dict()

async def on_connect(data, websocket):
    if len(PLAYERS) < 4:
        await register_player(data)
        # Welcome message is sent here
        await websocket.send("welcome_message")
    else:
        print("Session is full")

async def register_player(data):
    # Create a player object
    PLAYERS[uuid.uuid4()] = Player(data["nick"])
    message = "player_pos"
    await notify_players(message)

async def notify_players(message):
    if PLAYERS:
        await asyncio.wait([player.send(message) for player in PLAYERS])

async def create_game():
    pass

async def server(websocket, path):
    create_game()

    async for message in websocket:
        data = json.loads(message)
        if data["msg_code"] == "connect":
            # Add new player
            await on_connect(data, websocket)
            print(f'Number of players: {len(PLAYERS)}')
        elif data["msg_code"] == "player_move":
            pass
        elif data["msg_code"] == "player_plant_bomb":
            pass
        elif data["msg_code"] == "disconnect":
            # Remove player
            pass
        else:
            print("Unknown message.")

        


start_server = websockets.serve(server, "localhost", 5000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()