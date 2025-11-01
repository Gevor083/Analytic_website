from django.http import HttpResponse
from django.db import connections
from django.db.utils import OperationalError
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

def health_check(request):
    # Check database connection
    try:
        connections['default'].ensure_connection()
    except OperationalError:
        return HttpResponse('Database unavailable', status=503)

    # Check Redis connection
    try:
        redis_client = Redis.from_url('redis://redis:6379/0')
        redis_client.ping()
    except RedisConnectionError:
        return HttpResponse('Redis unavailable', status=503)

    return HttpResponse('OK', status=200)