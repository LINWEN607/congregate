from flask.views import MethodView
from flask import request

encoding = "utf-8"

class TestAPI(MethodView):
    route_prefix = "/test"

    def __init__(self, _, asset_name) -> None:
        self.asset_name = asset_name
    
    def get(self):
        return "Hello World!"