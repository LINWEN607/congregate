import sys
import os
from re import search
from pymongo import MongoClient, errors, DESCENDING
from gitlab_ps_utils.json_utils import stream_json_yield_to_file, read_json_file_into_object
from gitlab_ps_utils.file_utils import find_files_in_folder
from congregate.helpers.base_class import BaseClass


class MongoConnector(BaseClass):
    """
        Wrapper class for connecting to a mongo instance
    """

    def __init__(self, db=None, client=None):
        super().__init__()
        try:
            host = self.config.mongo_host
            port = self.config.mongo_port
            self.client = client(
                host=host, port=port) if client else MongoClient(
                host=host, port=port, maxPoolSize=500)
            self.db = self.client[db]
            self.client.server_info()
        except errors.ServerSelectionTimeoutError:
            self.log.error(
                f"ServerSelectionTimeoutError: Unable to connect to mongodb at {host}:{port}")
            sys.exit(os.EX_NOHOST)
        except errors.ConnectionFailure:
            self.log.error(
                f"ConnectionFailure: Unable to connect to mongodb at {host}:{port}")
            sys.exit(os.EX_UNAVAILABLE)

    def __setup_db(self):
        pass

    def create_unique_index(self, collection, key):
        return self.db[collection].create_index(key, unique=True)
    
    def create_collection_with_unique_index(self, collection, key):
        try:
            self.db.validate_collection(collection)
        except errors.OperationFailure:
            return self.create_unique_index(collection, key)

    def close_connection(self):
        self.db = None
        self.client.close()

    def insert_data(self, collection, data, bypass_document_validation=False):
        if isinstance(data, tuple):
            data = data[0]
        data = self.stringify_int_keys_in_dict(data)
        coll_type = collection.split("-")[0].upper()
        did = data.get("id")
        try:
            if isinstance(data, tuple):
                data = data[0]
            return self.db[collection].insert_one(
                data, bypass_document_validation=bypass_document_validation).inserted_id
        except errors.DuplicateKeyError as dke:
            self.log.debug(
                f"{coll_type} (ID: {did}) duplicate insert attempt. Aborting operation\n{dke}")
            return None
        except errors.DocumentTooLarge as dtl:
            self.log.error(
                f"{coll_type} (ID: {did}) document too large. Aborting operation\n{dtl}")
            return None

    def drop_collection(self, collection):
        self.log.info(f"Dropping {collection} collection")
        return self.db[collection].drop()

    def dump_collection_to_file(self, collection, path):
        self.log.info(f"Dumping {collection} collection to {path}")
        return stream_json_yield_to_file(
            path, self.stream_collection, collection)

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

    def wildcard_collection_query(self, pattern):
        return [c for c in self.db.list_collection_names() if (
            pattern in c and "noindex" not in c)]

    def ingest_json_file_into_mongo(self, file_path, collection=None):
        if not collection:
            collection = (search(r"(.+\/)(.+)\.json", file_path)).group(2)
        for data in read_json_file_into_object(file_path):
            self.insert_data(collection, data)

    def re_ingest_into_mongo(self, asset_type):
        for found_file in find_files_in_folder(
                asset_type, f"{self.app_path}/data"):
            if ".json" in found_file:
                self.ingest_json_file_into_mongo(
                    f"{self.app_path}/data/{found_file}")

    def safe_find_one(self, collection, query=None, **kwargs):
        """
            Helper method to get around mongomock bug in the unit tests
        """
        try:
            try:
                return self.db[collection].find_one(query, **kwargs)
            except TypeError:
                return self.db[collection].find_one(query)
        except errors.OperationFailure as e:
            # Condition for mongomock testing. Hints are not supported in
            # mongomock
            if "Unrecognized field 'hint'" in e._message:
                return self.db[collection].find_one(query)
            if "hint provided does not correspond to an existing index" in e._message:
                self.db[collection].rename(f"noindex-{collection}")
                self.log.warning(
                    f"Unindexed collection {collection} used with hint. Renaming collection to note no index")
                if "user" in collection:
                    self.user_collections = self.wildcard_collection_query(
                        "users")

    def safe_find(self, collection, query=None, **kwargs):
        """
            Helper method to get around mongomock bug in the unit tests
        """
        try:
            try:
                return self.db[collection].find(query, **kwargs)
            except TypeError:
                return self.db[collection].find(query)
        except errors.OperationFailure as e:
            # Condition for mongomock testing. Hints are not supported in
            # mongomock
            if "Unrecognized field 'hint'" in e._message:
                return self.db[collection].find(query)
            if "hint provided does not correspond to an existing index" in e._message:
                self.db[collection].rename(f"noindex-{collection}")
                self.log.warning(
                    f"Unindexed collection {collection} used with hint. Renaming collection to note no index")
                if "user" in collection:
                    self.user_collections = self.wildcard_collection_query(
                        "users")

    def clean_db(self, keys=False):
        for col in self.db.list_collection_names():
            # In order to preserve list of created deploy keys
            if not "keys-" in col or keys:
                self.drop_collection(col)
        self.__setup_db()

    def stringify_int_keys_in_dict(self, d):
        """
            Helper method to convert all int keys to strings
        """
        translate = {}
        for k, v in d.items():
            if isinstance(v, dict):
                self.stringify_int_keys_in_dict(v)
            if isinstance(k, int):
                translate[k] = str(k)
        for old, new in translate.items():
            d[new] = d.pop(old)
        return d

    def strip_dots_in_keys(self, d):
        """
            Helper method to replace all keys with dots to underscores
        """
        translate = {}
        for k, v in d.items():
            if isinstance(v, dict):
                self.strip_dots_in_keys(v)
            if '.' in k:
                translate[k] = k.replace(".", "_")
        for old, new in translate.items():
            d[new] = d.pop(old)
        return d

def mongo_connection(func):
    '''
        Decorator function to open and close a MongoDB connection
    '''
    def wrapper(*args, **kwargs):
        if 'mongo' in kwargs:
            return func(*args, **kwargs)
        else:
            mongo = MongoConnector()
            retval = func(*args, mongo=mongo, **kwargs)
            mongo.close_connection()
            return retval
    return wrapper
