import uuid
from .consumers import GameConsumer

# Allows any client to drawn on index.html                    
class GlobalConsumer(GameConsumer):
    async def connect(self):
        # Override only the parts that differ from a normal room
        self.room_id = "global"
        self.stream = "game:room:global"
        self.id = str(uuid.uuid4())

        # Now call the parent connect() which:
        # - accepts the socket
        # - sends snapshot of existing players
        # - starts the stream reader
        await super().connect()