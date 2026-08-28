from unittest.mock import patch
from mysite.redis import get_redis_client


def test_get_redis_client_returns_async_redis_instance():
    with patch("mysite.redis.redis.Redis") as mock_redis:
        client = get_redis_client()

        # Ensure Redis() constructor was called correctly
        mock_redis.assert_called_once_with(
            host="redis",
            port=6379,
            decode_responses=True,
        )

        # And ensure the returned client is whatever Redis() returned
        assert client is mock_redis.return_value
