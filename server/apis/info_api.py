from flask import Blueprint
from flask_cors import cross_origin
from server.apis.api_init import backstageInfo
from server.utils.message import HttpMessage
from server.config import Allow_Url_List

web_info = Blueprint('web_info', __name__)


@web_info.route("/index_notice/get", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getIndexNotice():
    """获取首页公告
   返回 json
   {
   "is_success":bool,
   "data": str base64 markdown
   """
    try:
        res = backstageInfo.getIndexNotice()
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@web_info.route("/record_number/get", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getRecordNumber():
    """获取备案号
   返回 json
   {
   "is_success":bool,
   "data": {}
   """
    try:
        res = backstageInfo.getRecordNumber()
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()
