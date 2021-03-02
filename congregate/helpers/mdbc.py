from re import search
from pymongo import MongoClient, errors
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import stream_json_yield_to_file, read_json_file_into_object, find_files_in_folder, strip_protocol


class MongoConnector(BaseClass):
    """
        Wrapper class for connecting to a mongo instance
    """

    CI_SOURCES = ["jenkins", "teamcity"]

    def __init__(self, host='localhost', port=27017, client=None):
        super(MongoConnector, self).__init__()
        try:
            self.client = client(
                host=host, port=port) if client else MongoClient(
                host=host, port=port, maxPoolSize=500)
            self.db = self.client.congregate
            self.client.server_info()
            self.__setup_db()
            self.user_collections = self.wildcard_collection_query("users")
        except errors.ServerSelectionTimeoutError:
            self.log.error(
                f"ServerSelectionTimeoutError: Unable to connect to mongodb at {host}:{port}")
            exit()
        except errors.ConnectionFailure:
            self.log.error(
                f"ConnectionFailure: Unable to connect to mongodb at {host}:{port}")
            exit()

    def __generate_collections_list(self):
        collections = []
        if self.config.source_host:
            src_hostname = strip_protocol(self.config.source_host)
            collections += [
                f"projects-{src_hostname}",
                f"groups-{src_hostname}",
                f"users-{src_hostname}"
            ]
        elif self.config.list_multiple_source_config("github_source"):
            for source in self.config.list_multiple_source_config(
                    "github_source"):
                src_hostname = strip_protocol(source.get('src_hostname', ""))
                collections += [
                    f"projects-{src_hostname}",
                    f"groups-{src_hostname}",
                    f"users-{src_hostname}"
                ]
        if tc_sources := self.config.list_ci_source_config(
                "teamcity_ci_source"):
            for tc in tc_sources:
                collections.append(
                    f"teamcity-{tc.get('tc_ci_src_hostname').split('//')[-1]}")
        if jenkins_sources := self.config.list_ci_source_config(
                "jenkins_ci_source"):
            for jenkins in jenkins_sources:
                collections.append(
                    f"jenkins-{jenkins.get('jenkins_ci_src_hostname').split('//')[-1]}")

        return collections

    def __setup_db(self):
        for collection in self.__generate_collections_list():
            if any(ci_source in collection for ci_source in self.CI_SOURCES):
                self.__create_unique_index(collection, "name")
                self.db[collection].create_index("url")
            else:
                self.__create_unique_index(collection, "id")
            if "user" in collection:
                self.db[collection].create_index("username")

    def __create_unique_index(self, collection, key):
        return self.db[collection].create_index(key, unique=True)

    def close_connection(self):
        self.db = None
        self.client.close()

    def insert_data(self, collection, data, bypass_document_validation=False):
        try:
            if isinstance(data, tuple):
                data = data[0]
            return self.db[collection].insert_one(data, bypass_document_validation=bypass_document_validation).inserted_id
        except errors.DuplicateKeyError:
            self.log.debug("Duplicate insert attempted. Aborting operation")
            return None

    def drop_collection(self, collection):
        return self.db[collection].drop()

    def dump_collection_to_file(self, collection, path):
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

    def find_user_email(self, username):
        for user_collection in self.user_collections:
            if query := self.safe_find_one(user_collection, query={
                                           "username": username}, hint="username_1"):
                return query.get("email", None)

    def ingest_json_file_into_mongo(self, file_path, collection=None):
        if not collection:
            collection = (search(r"(.+\/)(.+)\.json", file_path)).group(2)
        for data in read_json_file_into_object(file_path):
            self.insert_data(collection, data)

    def re_ingest_into_mongo(self, asset_type):
        for found_file in find_files_in_folder(asset_type):
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
            if "hint provided does not correspond to an existing index" in e._message():
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
            if "hint provided does not correspond to an existing index" in e._message():
                self.db[collection].rename(f"noindex-{collection}")
                self.log.warning(
                    f"Unindexed collection {collection} used with hint. Renaming collection to note no index")
                if "user" in collection:
                    self.user_collections = self.wildcard_collection_query(
                        "users")

    def clean_db(self):
        for col in self.db.list_collection_names():
            self.drop_collection(col)
        self.__setup_db()
