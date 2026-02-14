# Gunicorn Configuration for AutoAssistGroup Support System
# AWS EC2 Production Deployment

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:" + os.environ.get("PORT", "8000")
backlog = 2048

# Worker processes — use eventlet for socket.io WebSocket support
workers = 1  # eventlet uses cooperative multitasking, 1 worker handles many connections
worker_class = "eventlet"
worker_connections = 1000
timeout = 120
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging — filter out noisy socket.io polling from access log
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(t)s │ %(s)s │ %(m)s %(U)s │ %(D)sμs'

import logging

# Custom filter: suppress socket.io + static asset noise
class SocketIOFilter(logging.Filter):
    """Filter out socket.io polling and static file requests from access logs."""
    def filter(self, record):
        msg = record.getMessage()
        # Hide socket.io polling (the biggest source of noise)
        if '/socket.io/' in msg:
            return False
        # Hide static files
        if '/static/' in msg:
            return False
        return True


def on_starting(server):
    """Hook: runs when gunicorn master starts — install log filters."""
    pass

def post_fork(server, worker):
    """Hook: runs after each worker forks — install access log filter."""
    for handler in logging.getLogger('gunicorn.access').handlers:
        handler.addFilter(SocketIOFilter())

# Process naming
proc_name = "autoassist_support"

# Server mechanics
daemon = False
# pidfile = "/var/run/gunicorn/autoassist.pid"
# user = "www-data"
# group = "www-data"
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Environment variables
raw_env = [
    'FLASK_ENV=production',
    'FLASK_DEBUG=False',
]

# Preload app for better performance
preload_app = True

# Worker timeout for long-running requests
# (already set above)
# timeout = 120

# Graceful timeout
graceful_timeout = 30

# Forwarded allow ips (for nginx proxy)
forwarded_allow_ips = "127.0.0.1"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
