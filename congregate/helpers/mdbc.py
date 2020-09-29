from pymongo import MongoClient, errors
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import stream_json_yield_to_file

class MongoConnector(BaseClass):
    """
        Wrapper class for connecting to a mongo instance
    """
    def __init__(self, host='localhost', port=27017, client=None):
        super(MongoConnector, self).__init__()
        try:
            self.client = client(host=host, port=port) if client else MongoClient(host=host, port=port)
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

    def drop_collection(self, collection):
        return self.db[collection].drop()

    def dump_collection_to_file(self, collection, path):
        return stream_json_yield_to_file(path, self.stream_collection, collection)

    def stream_collection(self, collection):
        length = self.db[collection].count_documents({})
        count = 1
        for data in self.db[collection].find():
            data.pop("_id")
            if count < length:
                count += 1
                yield data, False
            else:
                yield data, True
