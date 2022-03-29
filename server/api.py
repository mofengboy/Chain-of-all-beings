import os
import sys
from flask import Flask, request
from flask_cors import cross_origin
import threading

sys.path.append("../")
sys.path.append(os.path.abspath("."))

from server.database import DB
from server.models import Auth, BlockOfBeings, MainNodeManager, ChainOfBeings
from server.utils.message import HttpMessage
from server.utils.ciphersuites import CipherSuites
from server.config import Allow_Url_List

api = Flask(__name__, static_url_path=None, static_folder='static')
db = DB()
auth = Auth(db=db)
blockOfBeings = BlockOfBeings(db)
mainNodeManager = MainNodeManager(db)
chainOfBlock = ChainOfBeings()


@api.route('/')
@cross_origin()
def hello_world():
    http_message = HttpMessage(is_success=True, data=["众生之链", "Web服务网址：https://beings.icu"])
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


@api.route("/main_node/new_apply/save", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def saveNewApply():
    """保存新申请书
    Content-Type: application/json
    {
      "captcha":{
              "uuid":"",
              "word"：“”
        }
      "node_id":str,
      "user_pk": str,
      "node_ip": str,
      "server_url": str,
      "node_create_time": str,
      "node_signature": str,
      "application": str,
      "application_signature": str,
      "remarks": str,
    }
    返回 json
    {
    "is_success":bool,
    "data": ""
    """
    try:
        info = request.get_json()
        # 验证码
        captcha = info["captcha"]
        if not auth.verifyCaptcha(uuid=captcha["uuid"], word=captcha["word"]):
            http_message = HttpMessage(is_success=False, data="验证码错误")
            return http_message.getJson()
        node_id = info["node_id"]
        user_pk = info["user_pk"]
        node_ip = info["node_ip"]
        server_url = info["server_url"]
        node_create_time = info["node_create_time"]
        node_signature = info["node_signature"]
        application = info["application"]
        application_signature = info["application_signature"]
        remarks = info["remarks"]
        if mainNodeManager.addApplicationForm(node_id, user_pk, node_ip, server_url, node_create_time, node_signature,
                                              application, application_signature, remarks):
            http_message = HttpMessage(is_success=True, data="保存成功")
            return http_message.getJson()
        else:
            http_message = HttpMessage(is_success=False, data="服务端签名校验失败，保存失败")
            return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@api.route("/chain/beings/get", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getBeingsOfChain():
    """获取众生链区块
   Content-Type: application/json
   {
     ?db_id=1
   }
   返回 json
   {
   "is_success":bool,
   "data": {
            "id": "",
            "block_id": "",
            "epoch": "",
            "prev_block": "",
            "prev_block_header": "",
            "user_pk": "",
            "body_signature": "",
            "body": "",
            "timestamp":""
        }
   """
    try:
        db_id = request.args.get("db_id")
        block_dict = chainOfBlock.getBlockByID(db_id)
        http_message = HttpMessage(is_success=True, data=block_dict)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@api.route("/chain/beings_list/get", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getBeingsListOfChain():
    """获取众生链区块ID列表
   {
     ?start=0&end=8
   }
   返回 json
   {
   "is_success":bool,
   "data": [id...]
   """
    try:
        start = int(request.args.get("start"))
        end = int(request.args.get("end"))
        if start - end > 8:
            http_message = HttpMessage(is_success=False, data="每次最多查询8个Epoch的区块")
            return http_message.getJson()
        id_list = chainOfBlock.getIDListOfBlockByEpoch(start=start, end=end)
        http_message = HttpMessage(is_success=True, data=id_list)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@api.route("/chain/beings/epoch_list", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getEpochListOfBeingsChain():
    """获取众生链区块Epoch列表
   {
     ?offset=0&count=8
   }
   返回 json
   {
   "is_success":bool,
   "data": [id...]
   """
    try:
        offset = int(request.args.get("start"))
        count = int(request.args.get("end"))
        if count > 1024:
            http_message = HttpMessage(is_success=False, data="每次最多查询1024个Epoch列表")
            return http_message.getJson()
        epoch_list = chainOfBlock.getEpochLIst(offset, count)
        http_message = HttpMessage(is_success=True, data=epoch_list)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@api.route("/chain/beings/max_epoch", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getMaxEpoch():
    """获取众生链区块最大期次
   返回 json
   {
   "is_success":bool,
   "data": int
   """
    try:
        epoch = chainOfBlock.getMaxEpoch()
        http_message = HttpMessage(is_success=True, data=epoch)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


# 以下为后台接口，需要权限认证
# 登录
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
        http_message = HttpMessage(is_success=False, data=err)
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


@api.route("/backstage/main_node/new_apply_list/get", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def getNewApplyList():
    """获取通过此主节点申请成为主节点的申请书列表
    Content-Type: application/json
    {
      "token":"",
      "offset":int,
      "count": int,
    }
    返回 json
    {
    "is_success":bool,
    "data": [{'db_id': 1, 'crate_time': '16453453280.98137'}]
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
        res = mainNodeManager.getApplicationListOfMainNode(offset, count)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@api.route("/backstage/main_node/other_apply_list/get", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def getOtherApplyList():
    """获取通过其他主节点申请成为主节点的申请书列表
    Content-Type: application/json
    {
      "token":"",
      "offset":int,
      "count": int,
    }
    返回 json
    {
    "is_success":bool,
    "data": [{'db_id': 1, 'crate_time': '16453453280.98137'}]
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
        res = mainNodeManager.getApplicationOfOtherMainNode(offset, count)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@api.route("/backstage/main_node/new_apply/get", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def getNewApply():
    """获取通过此主节点申请成为主节点的申请书
    Content-Type: application/json
    {
      "token":"",
      "db_id":int
    }
    返回 json
    {
    "is_success":bool,
    "data": {'db_id': 1, 'crate_time': '16453453280.98137'....}
    """
    try:
        info = request.get_json()
        # 验证token
        token = info["token"]
        if not auth.verifyToken(token):
            http_message = HttpMessage(is_success=False, data="Token无效")
            return http_message.getJson()
        db_id = info["db_id"]
        res = mainNodeManager.getApplicationFormByDBId(db_id)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@api.route("/backstage/main_node/other_apply/get", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def getOtherApply():
    """获取通过其他主节点申请成为主节点的申请书
    Content-Type: application/json
    {
      "token":"",
      "db_id":int
    }
    返回 json
    {
    "is_success":bool,
    "data": {'db_id': 1, 'crate_time': '16453453280.98137'....}
    """
    try:
        info = request.get_json()
        # 验证token
        token = info["token"]
        if not auth.verifyToken(token):
            http_message = HttpMessage(is_success=False, data="Token无效")
            return http_message.getJson()
        db_id = info["db_id"]
        res = mainNodeManager.getOtherNodeApplicationFormByDBId(db_id)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@api.route("/backstage/main_node/new_apply/review", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def reviewNewApply():
    """审核通过当前主节点申请成为主节点的申请书
    Content-Type: application/json
    {
      "token":"",
      "db_id":int,
      "review":int,
    }
    返回 json
    {
    "is_success":bool,
    "data": ”“
    """
    try:
        info = request.get_json()
        # 验证token
        token = info["token"]
        if not auth.verifyToken(token):
            http_message = HttpMessage(is_success=False, data="Token无效")
            return http_message.getJson()
        db_id = info["db_id"]
        review = info["is_review"]
        mainNodeManager.reviewApplicationFormByDBId(db_id, review)
        http_message = HttpMessage(is_success=True, data="审核完成")
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@api.route("/backstage/main_node/other_apply/review", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def reviewOtherApply():
    """审核通过其他主节点申请成为主节点的申请书
    Content-Type: application/json
    {
      "token":"",
      "db_id":int,
      "review":int,
    }
    返回 json
    {
    "is_success":bool,
    "data": ”“
    """
    try:
        info = request.get_json()
        # 验证token
        token = info["token"]
        if not auth.verifyToken(token):
            http_message = HttpMessage(is_success=False, data="Token无效")
            return http_message.getJson()
        db_id = info["db_id"]
        review = info["review"]
        mainNodeManager.reviewOtherNodeApplicationFormByDBId(db_id, review)
        http_message = HttpMessage(is_success=True, data="审核完成")
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
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
