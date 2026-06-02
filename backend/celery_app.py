"""Celery application: Redis broker/backend plus queue routing for the two pipelines.

Tasks are routed to the ``data-processing-pipeline`` and ``forecasting-pipeline``
queues, which the corresponding worker services consume.
"""
from celery import Celery
from global_config import REDIS_IP, REDIS_PORT

celery_client = Celery('scheduler', broker=f'redis://{REDIS_IP}:{REDIS_PORT}',
                       backend=f'redis://{REDIS_IP}:{REDIS_PORT}')
celery_client.conf.update({
    'broker_url': f'redis://{REDIS_IP}:{REDIS_PORT}',
    'import': ['tasks'],
    'task_routes': {
        'outlier_wrapper': {
            'queue': 'data-processing-pipeline'
        },
        'imputer_wrapper': {
            'queue': 'data-processing-pipeline'
        },
        'simple_forecasting': {
            'queue': 'forecasting-pipeline'
        }
    },
    'task_serializer': 'json',
    'result_serializer': 'json',
    'accept_content': ['json']
})
