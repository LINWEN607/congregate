from celery import shared_task
from congregate.helpers.mdbc import MongoConnector


class CeleryMongoConnector(MongoConnector):
    """
        Wrapper class for connecting to the Celery job DB in Mongo
    """

    def __init__(self, client=None):
        super().__init__(db='jobs', client=client)

def mongo_connection(func):
    '''
        Decorator function to open and close a MongoDB connection
    '''
    def wrapper(*args, **kwargs):
        if 'mongo' in kwargs:
            return func(*args, **kwargs)
        else:
            mongo = CeleryMongoConnector()
            retval = func(*args, mongo=mongo, **kwargs)
            mongo.close_connection()
            return retval
    return wrapper

@shared_task(name='dump-collection-to-file')
@mongo_connection
def dump_collection_to_file_task(collection, path, mongo=None):
    return mongo.dump_collection_to_file(collection, path)
