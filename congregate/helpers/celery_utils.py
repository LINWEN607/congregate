from dataclasses import dataclass, asdict
from flask import Flask
from celery import Celery, Task
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
        task_ignore_results=True
    ).to_dict()

@dataclass
class CeleryConfig():
    broker_url: str
    result_backend: str
    task_ignore_results: bool

    def to_dict(self):
        return asdict(self)