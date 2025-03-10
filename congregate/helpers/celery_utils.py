import atexit
from dataclasses import dataclass, asdict
from flask import Flask
from celery import Celery, Task, states
from celery.result import AsyncResult
from celery.signals import worker_shutdown, celeryd_init
from redis import Redis
from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.helpers.celery_mdbc import mongo_connection

FINISHED_STATES = [states.FAILURE, states.REVOKED, states.SUCCESS]

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
        },
        worker_concurrency=c.processes
    ).to_dict()

@worker_shutdown.connect
def cleanup_queue(sender, **kwargs):
    '''
        Flushes the redis cache when Celery shuts down
    '''
    flush_redis_cache()

@celeryd_init.connect
def register_flush_atexit(sender, **kwargs):
    '''
        Register an atexit handler as additional insurance
    '''
    atexit.register(flush_redis_cache)

def flush_redis_cache():
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
            
@mongo_connection
def find_pending_tasks(tasks, mongo=None):
    return mongo.safe_find('celery_taskmeta', {
        'task': {
            '$in': tasks
        }, 
        'status': {
            '$in': ['PENDING', 'STARTED']
        }
    })

@mongo_connection
def get_task_by_id(id, mongo=None):
    return mongo.safe_find_one('celery_taskmeta', {"_id": id})

def get_task_chain_status(id):
    if res := get_task_by_id(id):
        if parent := res.get('parent_id'):
            res = get_task_status(parent)
        else:
            return get_task_status(id)
        if res.children:
            child_not_finished = False
            for child in res.children:
                if child.state not in FINISHED_STATES:
                    child_not_finished = True
            if child_not_finished:
                return states.PENDING
            else:
                return res.state
        else:
            return states.PENDING

@dataclass
class CeleryConfig():
    broker_url: str
    result_backend: str
    task_ignore_results: bool
    task_track_started: bool
    result_extended: bool
    override_backends: dict
    worker_concurrency: int

    def to_dict(self):
        return asdict(self)
