import os
import sys
from flask import Flask
from flask_cors import cross_origin
import threading

sys.path.append("../")
sys.path.append(os.path.abspath("."))
from server.apis.chain_api import chain
from server.apis.backstage_api import backstage
from server.apis.info_api import web_info
from server.utils.message import HttpMessage
from server.config import Allow_Url_List

api = Flask(__name__, static_url_path=None, static_folder='static')
api.register_blueprint(backstage)
api.register_blueprint(web_info)
api.register_blueprint(chain)


@api.route('/')
@cross_origin(origins=Allow_Url_List)
def hello_world():
    http_message = HttpMessage(is_success=True, data=["众生之链", "Web服务网址：" + Allow_Url_List[0]])
    return http_message.getJson()


# 404页面
@api.errorhandler(404)
def notFound(e):
    http_message = HttpMessage(is_success=False, data="404")
    return http_message.getJson()


class WebServer(threading.Thread):
    def run(self) -> None:
        api.run()


if __name__ == '__main__':
    api.run(host="0.0.0.0")
