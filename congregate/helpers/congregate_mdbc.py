
from pymongo import DESCENDING
from celery import shared_task
from gitlab_ps_utils.misc_utils import strip_netloc
from congregate.helpers.mdbc import MongoConnector


class CongregateMongoConnector(MongoConnector):
    """
        Wrapper class for connecting to the Congregate metadata DB in Mongo
    """

    CI_SOURCES = ["jenkins", "teamcity"]

    def __init__(self, client=None):
        super().__init__(db='congregate', client=client)
        self.__setup_db()
        self.user_collections = self.wildcard_collection_query("users")
        self.DESCENDING = DESCENDING

    def __generate_collections_list(self):
        collections = []
        if self.config.source_host:
            src_hostname = strip_netloc(self.config.source_host)
            collections += [
                f"projects-{src_hostname}",
                f"groups-{src_hostname}",
                f"users-{src_hostname}",
                f"keys-{src_hostname}"
            ]
        elif self.config.list_multiple_source_config("github_source"):
            for source in self.config.list_multiple_source_config(
                    "github_source"):
                src_hostname = strip_netloc(source.get('src_hostname', ""))
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
                self.create_unique_index(collection, "name")
                self.db[collection].create_index("url")
            else:
                self.create_unique_index(collection, "id")
            if "user" in collection:
                self.db[collection].create_index("username")

    def find_user_email(self, username):
        for user_collection in self.user_collections:
            if query := self.safe_find_one(
                user_collection,
                query={
                    "username": username
                },
                hint="username_1"
            ):
                return query.get("email", None)

    def clean_db(self, keys=False):
        for col in self.db.list_collection_names():
            # In order to preserve list of created deploy keys
            if not "keys-" in col or keys:
                self.drop_collection(col)
        self.__setup_db()

def mongo_connection(func):
    '''
        Decorator function to open and close a MongoDB connection
    '''
    def wrapper(*args, **kwargs):
        if 'mongo' in kwargs:
            return func(*args, **kwargs)
        else:
            mongo = CongregateMongoConnector()
            retval = func(*args, mongo=mongo, **kwargs)
            mongo.close_connection()
            return retval
    return wrapper

@shared_task(name='dump-collection-to-file')
@mongo_connection
def dump_collection_to_file_task(collection, path, mongo=None):
    return mongo.dump_collection_to_file(collection, path)
