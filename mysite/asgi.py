import os
import asyncio
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import core.routing
from django.core.asgi import get_asgi_application
from rooms.services import purge_all_rooms

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

django_asgi_app = get_asgi_application()

# Lifespan to ensure proper startup order when using Daphne in production
async def lifespan(scope, receive, send):
    if scope["type"] == "lifespan":
        # Startup
        if os.environ.get("RUN_PURGE_ON_STARTUP") == "true":
            print("🔥 ASGI lifespan: starting purge_all_rooms()")
            asyncio.create_task(purge_all_rooms())

        # Tell server startup is complete
        await send({"type": "lifespan.startup.complete"})

        # Wait for shutdown
        while True:
            message = await receive()
            if message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(core.routing.websocket_urlpatterns)
    ),
    "lifespan": lifespan,
})
