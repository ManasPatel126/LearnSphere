"""
RQ worker — run this in a separate terminal alongside Flask.

    python worker.py

It listens on the 'phase1' queue and processes decompose tasks.
"""

import os
from redis import Redis
from rq import Worker, Queue, Connection
from dotenv import load_dotenv

load_dotenv()

redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker(queues=[Queue("phase1", connection=redis_conn)])
        worker.work(with_scheduler=True)
