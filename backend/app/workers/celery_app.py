from celery import Celery

from app.config import settings

celery_app = Celery("jm_camera", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_default_queue = "jm_camera"
