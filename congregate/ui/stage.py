from flask.views import MethodView
from flask import request

encoding = "utf-8"

class StageAPI(MethodView):
    route_prefix = "/stage"

    def __init__(self, client, asset_name) -> None:
        self.client = client
        self.asset_name = asset_name
    
    def post(self):
        data = request.get_data().decode(encoding).split(",")
        self.client.stage_data(data, dry_run=False)
        return self.__message(data, self.asset_name)
    
    def __message(self, obj, obj_type):
        num = len(obj)
        return f"Staged {num} {obj_type}{'s' if num > 1 or num == 0 else ''}"
