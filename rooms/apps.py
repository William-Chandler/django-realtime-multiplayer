from django.apps import AppConfig
import threading
import os
import asyncio

class RoomsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rooms"

    def ready(self):
        from rooms.services import purge_all_rooms

        print("🔥 RoomsConfig.ready() called")

        # Only run in the final process
        if os.environ.get("RUN_MAIN") != "true":
            print("⚠️ Not main process, skipping purge")
            return

        if os.environ.get("RUN_PURGE_ON_STARTUP") == "true":
            print("🔥 Starting purge thread")

            def run_purge():
                asyncio.run(purge_all_rooms())

            threading.Thread(target=run_purge, daemon=True).start()
