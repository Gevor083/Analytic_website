"""
Rate-limit middleware to prevent brute-force on login/register endpoints.

Configuration (settings.py, all optional):
    RATE_LIMIT_WINDOW   = 60    # seconds
    RATE_LIMIT_MAX      = 20    # max requests per window per IP
    RATE_LIMIT_PATHS    = ['/login/', '/register/', '/face-login/']
"""

import logging
import time
from collections import defaultdict
from threading import Lock

from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

# In-memory rate limit store (per process; good for single-server dev/prod).
# For multi-process deployments, swap this dict for a Redis-backed counter.
_store: dict = defaultdict(list)  # ip → [timestamp, ...]
_lock  = Lock()

WINDOW   = getattr(settings, 'RATE_LIMIT_WINDOW',  60)   # seconds
MAX_HITS = getattr(settings, 'RATE_LIMIT_MAX',      20)
PATHS    = getattr(settings, 'RATE_LIMIT_PATHS', ['/login/', '/register/', '/face-login/'])


class RateLimitMiddleware(MiddlewareMixin):
    """Sliding-window rate limiter for configured URL paths."""

    def process_request(self, request):
        if request.method != 'POST':
            return None                  # only limit POST (login forms)

        if not any(request.path.startswith(p) for p in PATHS):
            return None

        ip  = self._get_ip(request)
        now = time.time()

        with _lock:
            hits = _store[ip]
            # Evict expired timestamps
            hits[:] = [t for t in hits if now - t < WINDOW]
            if len(hits) >= MAX_HITS:
                logger.warning("Rate limit exceeded for IP %s on %s", ip, request.path)
                retry_after = int(WINDOW - (now - hits[0]))
                if request.headers.get('Accept', '').startswith('application/json'):
                    resp = JsonResponse(
                        {'error': 'Too many requests. Please wait before trying again.'},
                        status=429,
                    )
                else:
                    from django.shortcuts import render
                    resp = render(request, 'analytics_app/rate_limited.html',
                                  {'retry_after': retry_after}, status=429)
                resp['Retry-After'] = str(retry_after)
                return resp

            hits.append(now)
            _store[ip] = hits
            return None

    @staticmethod
    def _get_ip(request) -> str:
        """Return the real client IP, respecting X-Forwarded-For."""
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
