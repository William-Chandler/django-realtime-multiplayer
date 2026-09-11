import redis.asyncio as redis

def get_redis_client():
    return redis.Redis(
        host="redis",
        port=6379,
        decode_responses=True,
	socket_timeout=None,          # no read timeout
        socket_connect_timeout=5,     # reasonable connect timeout
        retry_on_timeout=True,        # auto-retry on read timeout
    )
