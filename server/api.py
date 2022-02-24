from flask import Flask, request

from server.database import DB
from server.models import Auth, BlockOfBeings
from server.utils.message import HttpMessage

api = Flask(__name__)
db = DB()
auth = Auth(db=db)
blockOfBeings = BlockOfBeings(db)


@api.route('/')
def hello_world():
    http_message = HttpMessage(is_success=True, data="众生之链")
    return http_message.getJson()


@api.route('/block/beings/save', methods=['POST'])
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
            # if not auth.verifyCaptcha(uuid=captcha["uuid"], word=captcha["word"]):
            #     http_message = HttpMessage(is_success=False, data="验证码错误")
            #     return http_message.getJson()
            user_pk = info["user_pk"]
            body = info["body"]
            signature = info["signature"]
            res = blockOfBeings.addBlock(user_pk=user_pk, body=body, signature=signature)
            http_message = HttpMessage(is_success=res, data="")
            return http_message.getJson()

        except Exception as err:
            # print(err)
            http_message = HttpMessage(is_success=False, data="参数错误")
            return http_message.getJson()


# 获取验证码
@api.route("/captcha/get", methods=['POST'])
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
            # if not auth.verifyCaptcha(uuid=captcha["uuid"], word=captcha["word"]):
            #     http_message = HttpMessage(is_success=False, data="验证码错误")
            #     return http_message.getJson()
            username = info["username"]
            password = info["password"]
            token = auth.generateTokenByUsernameAndPassword(username=username, password=password)
            if token == "false":
                http_message = HttpMessage(is_success=False, data="用户名或密码错误")
                return http_message.getJson()
            else:
                res = {
                    "token": token
                }
                http_message = HttpMessage(is_success=True, data=res)
                return http_message.getJson()
        except Exception as err:
            # print(err)
            http_message = HttpMessage(is_success=False, data="参数错误")
            return http_message.getJson()


@api.route("/backstage/beings_list/get", methods=['POST'])
def getBeingList():
    """获取待审核众生区块列表
        Content-Type: application/json
        {
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
        res = blockOfBeings.getBlockList(count)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        # print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@api.route("/backstage/beings/get", methods=['POST'])
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
        # print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


if __name__ == '__main__':
    api.run()
