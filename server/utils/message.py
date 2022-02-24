import json


class HttpMessage:
    def __init__(self, is_success, data):
        self.isSuccess = is_success
        self.data = data

    def getJson(self):
        info = {
            "is_success": self.isSuccess,
            "data": self.data
        }
        return json.dumps(info, ensure_ascii=False)
