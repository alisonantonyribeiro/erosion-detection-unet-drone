from celery import Celery

from config.settings import get_settings

celery_app = Celery(
    "erosion",
    broker=get_settings().redis_url,
    backend=get_settings().redis_url,
)
celery_app.autodiscover_tasks(["workers"])
