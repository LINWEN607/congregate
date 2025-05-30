from requests import Response

from congregate.helpers.congregate_mdbc import CongregateMongoConnector


class DbOrHttpMixin():
    """
        Mixin to help switch between HTTP requests or storing POST
        request payloads to Mongo
    """
    default_collection = "project_features"

    def send_data(self, req_func, params, key, src_id, data, airgap=False, airgap_export=False, mongo_coll=default_collection):
        if airgap and airgap_export:
            resp = Response()
            resp.status_code = 100
            try:
                mongo = CongregateMongoConnector()
                mongo.db[mongo_coll].update_one(
                    {'id': src_id},
                    {'$push': {key: data}},
                    upsert=True)
                mongo.close_connection()
                resp.status_code = 201
            except Exception as e:
                resp.status_code = 500
                resp.text = e
            return resp
        return req_func(*params, data)

    def get_data(self, req_func, params, key, src_id, airgap=False, airgap_import=False, mongo_coll=default_collection):
        if airgap and airgap_import:
            mongo = CongregateMongoConnector()
            record = mongo.safe_find_one(mongo_coll, {
                'id': src_id
            })
            mongo.close_connection()
            return record.get(key)
        return req_func(*params)
