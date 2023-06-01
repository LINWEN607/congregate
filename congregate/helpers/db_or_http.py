from congregate.helpers.mdbc import MongoConnector

class DbOrHttpMixin():
    """
        Mixin to help switch between HTTP requests or storing POST
        request payloads to Mongo
    """
    default_collection = "project_features"

    def send_data(self, req_func, params, key, src_id, data, airgap=False, mongo_coll=default_collection):
        if airgap:
            mongo = MongoConnector()
            mongo.db[mongo_coll].update_one(
                {'id': src_id}, 
                {'$push': {key: data}}, 
                upsert=True)
            mongo.close_connection()
        else:
            req_func(*params, data)
    
    def get_data(self, req_func, params, key, src_id, data, airgap=False, mongo_coll=default_collection):
        if airgap:
            mongo = MongoConnector()
            record = mongo.safe_find_one(mongo_coll, {
                'id': src_id
            })
            mongo.close_connection()
            return record.get(key)
        else:
            return req_func(*params, data)
