import os
import sys
from flask import Flask, request
from flask_cors import cross_origin
import threading

sys.path.append("../")
sys.path.append(os.path.abspath("."))

from server.database import DB
from server.models import Auth, BlockOfBeings
from server.utils.message import HttpMessage
from server.utils.ciphersuites import CipherSuites
from server.config import Allow_Url_List

api = Flask(__name__)
db = DB()
auth = Auth(db=db)
blockOfBeings = BlockOfBeings(db)


@api.route('/')
@cross_origin()
def hello_world():
    http_message = HttpMessage(is_success=True, data="众生之链")
    return http_message.getJson()


@api.route('/block/beings/save', methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def block_of_beings_save():
    """申请创建众生区块
        Content-Type: application/json
        {
          "user_pk": "",
          "body": "",
          "signature": "",
          "captcha":{
              "uuid":"",
              "word"：“”
          }
        }
        返回 json
        {
        "is_success":bool,
        "data":""
        """
    if request.method == 'POST':
        info = request.get_json()
        try:
            captcha = info["captcha"]
            if not auth.verifyCaptcha(uuid=captcha["uuid"], word=captcha["word"]):
                http_message = HttpMessage(is_success=False, data="验证码错误")
                return http_message.getJson()
            user_pk = info["user_pk"]
            body = info["body"]
            signature = info["signature"]

        except Exception as err:
            print(err)
            http_message = HttpMessage(is_success=False, data="参数错误")
            return http_message.getJson()

        # 验证签名
        if not CipherSuites.verify(pk=user_pk, signature=signature, message=str(body).encode("utf-8")):
            http_message = HttpMessage(is_success=False, data="签名验证失败")
            return http_message.getJson()

        # 存到数据库
        res = blockOfBeings.addBlock(user_pk=user_pk, body=body, signature=signature)
        http_message = HttpMessage(is_success=res, data="申请创建成功")
        return http_message.getJson()


# 获取验证码
@api.route("/captcha/get", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def get_captcha():
    """
    Content-Type: application/json

    返回 json
    {
    "is_success":bool,
    "data":{
        "uuid": "",
        "pic_base64": ""
        }
    }
    """
    res = auth.getCaptcha()
    http_message = HttpMessage(is_success=True, data=res)
    return http_message.getJson()


# 以下为后台接口，需要权限认证
@api.route("/backstage/login", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def login():
    """后台用户登录
        Content-Type: application/json
        {
          "username": "",
          "password": "",
          "captcha":{
              "uuid":"",
              "word"：“”
          }
        }
        返回 json
        {
        "is_success":bool,
        "data":{
            "token": ""
        }
        """
    if request.method == 'POST':
        info = request.get_json()
        try:
            captcha = info["captcha"]
            if not auth.verifyCaptcha(uuid=captcha["uuid"], word=captcha["word"]):
                http_message = HttpMessage(is_success=False, data="验证码错误")
                return http_message.getJson()
            username = info["username"]
            password = info["password"]
            token = auth.generateTokenByUsernameAndPassword(username=username, password=password)
            if token == "false":
                http_message = HttpMessage(is_success=False, data="用户名或密码错误")
                return http_message.getJson()
            else:
                http_message = HttpMessage(is_success=True, data=token)
                return http_message.getJson()
        except Exception as err:
            print(err)
            http_message = HttpMessage(is_success=False, data="参数错误")
            return http_message.getJson()


@api.route("/backstage/token/verify", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def verifyToken():
    """验证token
        Content-Type: application/json
        {
          "token": ""
        }
        返回 json
        {
        "is_success":bool,
        "data":""
        """
    try:
        info = request.get_json()
        token = info["token"]
        if not auth.verifyToken(token):
            http_message = HttpMessage(is_success=False, data="Token无效")
            return http_message.getJson()
        else:
            http_message = HttpMessage(is_success=True, data="Token有效")
            return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@api.route("/backstage/beings_list/get", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def getBeingList():
    """获取待审核众生区块列表
        Content-Type: application/json
        {
          "count": int,
          "token":""
        }
        or
        {
          "offset":int,
          "count": int,
          "token":""
        }
        返回 json
        {
        "is_success":bool,
        "data":[
            {'db_id': 2, 'crate_time': '1645617280.98137'},....
            ]
        """
    try:
        info = request.get_json()
        # 验证token
        token = info["token"]
        if not auth.verifyToken(token):
            http_message = HttpMessage(is_success=False, data="Token无效")
            return http_message.getJson()
        # 获取列表
        count = info["count"]
        try:
            offset = info["offset"]
        except Exception:
            offset = None
        res = blockOfBeings.getBlockList(offset, count)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@api.route("/backstage/waiting_beings_list/get", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def getWaitingBeingList():
    """获取待发布众生区块列表
        Content-Type: application/json
        {
          "offset":int,
          "count": int,
          "token":""
        }
        返回 json
        {
        "is_success":bool,
        "data":[
            {'db_id': 2, 'crate_time': '1645617280.98137'},....
            ]
        """
    try:
        info = request.get_json()
        # 验证token
        token = info["token"]
        if not auth.verifyToken(token):
            http_message = HttpMessage(is_success=False, data="Token无效")
            return http_message.getJson()
        # 获取列表
        count = info["count"]
        offset = info["offset"]
        res = blockOfBeings.getWaitingBlockList(offset, count)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@api.route("/backstage/beings/get", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def getBeings():
    """获取众生区块详细信息
        Content-Type: application/json
        {
          "db_id": int,
          "token":""
        }
        返回 json
        {
        "is_success":bool,
        "data": {'db_id': 2, 'crate_time': '1645617280.98137'....}
        """
    try:
        info = request.get_json()
        # 验证token
        token = info["token"]
        if not auth.verifyToken(token):
            http_message = HttpMessage(is_success=False, data="Token无效")
            return http_message.getJson()
        # 获取列表
        db_id = info["db_id"]
        res = blockOfBeings.getBlockByDBId(db_id)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@api.route("/backstage/beings/audit", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def auditBeings():
    """审核众生区块
        Content-Type: application/json
        {
          "db_id": int,
          "token":"",
          "is_review":int
        }
        返回 json
        {
        "is_success":bool,
        "data": {'db_id': 2, 'crate_time': '1645617280.98137'....}
        """
    try:
        info = request.get_json()
        # 验证token
        token = info["token"]
        if not auth.verifyToken(token):
            http_message = HttpMessage(is_success=False, data="Token无效")
            return http_message.getJson()
        # 获取列表
        db_id = info["db_id"]
        is_review = info["is_review"]
        blockOfBeings.reviewBlock(db_id, is_review)
        http_message = HttpMessage(is_success=True, data="修改成功")
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


class WebServer(threading.Thread):
    def run(self) -> None:
        api.run()


if __name__ == '__main__':
    api.run()
