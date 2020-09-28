from pymongo import MongoClient, errors
from congregate.helpers.base_class import BaseClass

class MongoConnector(BaseClass):
    """
        Wrapper class for connecting to a mongo instance
    """
    def __init__(self, host='localhost', port=27017):
        super(MongoConnector, self).__init__()
        try:
            self.client = MongoClient(port=port, host=host)
            self.db = self.client.congregate
            self.client.server_info()
            self.__setup_db()
        except errors.ServerSelectionTimeoutError:
            self.log.error("ServerSelectionTimeoutError: Unable to connect to mongodb at %s:%s" % (host, port))
            exit()
        except errors.ConnectionFailure:
            self.log.error("ConnectionFailure: Unable to connect to mongodb at %s:%s" % (host, port))
            exit()
    
    def get_client(self):
        return self.client
    
    def get_db(self):
        return self.db
    
    def __setup_db(self):
        collections = ["projects", "groups", "users"]
        for collection in collections:
            self.__create_unique_index(collection, "id")

    def __create_unique_index(self, collection, key):
        return self.db[collection].create_index(key, unique=True)
    
    def insert_data(self, collection, data):
        try:
            return self.db[collection].insert_one(data).inserted_id
        except errors.DuplicateKeyError:
            self.log.debug("Duplicate insert attempted. Aborting operation")
            return None
    
