from dataclasses import dataclass, asdict
from flask import Flask
from celery import Celery, Task
from celery.result import AsyncResult
from celery.signals import worker_process_shutdown
from redis import Redis
from congregate.helpers.configuration_validator import ConfigurationValidator

def celery_init_app(app: Flask) -> Celery:
    """
        Initializes a Celery worker app within Flask
    """
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

def generate_celery_config():
    c = ConfigurationValidator()
    return CeleryConfig(
        broker_url=f"redis://:password@{c.redis_host}:{c.redis_port}/0",
        result_backend=f"mongodb://{c.mongo_host}:{c.mongo_port}/jobs",
        task_ignore_results=True,
        task_track_started=True,
        result_extended=False,
        override_backends={
            "mongodb": "congregate.helpers.extended_mongo_backend:ExtendedMongoBackend"
        }
    ).to_dict()

@worker_process_shutdown.connect
def cleanup_queue():
    c = ConfigurationValidator()
    r = Redis(host=c.redis_host, port=c.redis_port, password='password')
    print("Flushing redis cache")
    r.flushall()
    r = None
    
def get_task_status(id):
    return AsyncResult(id)

def find_arg_prop(res: AsyncResult, prop_key: str):
    '''
        Super simple dict key value lookup across an tuple of arguments

        This does not dig into a nested dictionary
    '''
    if res.args:
        for arg in res.args:
            if isinstance(arg, dict):
                return arg.get(prop_key)

@dataclass
class CeleryConfig():
    broker_url: str
    result_backend: str
    task_ignore_results: bool
    task_track_started: bool
    result_extended: bool
    override_backends : dict

    def to_dict(self):
        return asdict(self)
