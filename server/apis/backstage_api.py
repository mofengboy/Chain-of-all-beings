from flask import request, Blueprint
from flask_cors import cross_origin
from server.apis.api_init import auth, backstageInfo, blockOfBeings, blockOfTimes, blockOfGarbage, mainNodeManager, vote
from server.utils.message import HttpMessage
from server.config import Allow_Url_List

backstage = Blueprint('backstage', __name__)


# 登录
@backstage.route("/backstage/login", methods=['POST'])
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


@backstage.route("/backstage/token/verify", methods=['POST'])
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


@backstage.route("/backstage/index_notice/modify", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def modifyIndexNotice():
    """修改首页公告
    Content-Type: application/json
        {
          "token": "",
          "content":""
        }
   返回 json
   {
   "is_success":bool,
   "data": str base64 markdown
   }
   """
    try:
        info = request.get_json()
        token = info["token"]
        if not auth.verifyToken(token):
            http_message = HttpMessage(is_success=False, data="Token无效")
            return http_message.getJson()
        content = info["content"]
        res = backstageInfo.modifyIndexNotice(content)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@backstage.route("/backstage/record_number/set", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def setRecordNumber():
    """设置备案号
    Content-Type: application/json
        {
          "token": "",
          "record_number":""
        }
   返回 json
   {
   "is_success":bool,
   "data": {}
   }
   """
    try:
        info = request.get_json()
        token = info["token"]
        if not auth.verifyToken(token):
            http_message = HttpMessage(is_success=False, data="Token无效")
            return http_message.getJson()
        record_number = info["record_number"]
        res = backstageInfo.setRecordNumber(record_number)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@backstage.route("/backstage/beings_list/get", methods=['POST'])
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


@backstage.route("/backstage/waiting_beings_list/get", methods=['POST'])
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


@backstage.route("/backstage/beings/get", methods=['POST'])
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


@backstage.route("/backstage/beings/audit", methods=['POST'])
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


@backstage.route("/backstage/beings/recommend", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def recommendBeings():
    """推荐众生区块
        Content-Type: application/json
        {
          "token":"",
          "block_id":""
        }
        返回 json
        {
        "is_success":bool,
        "data":
        """
    try:
        info = request.get_json()
        # 验证token
        token = info["token"]
        if not auth.verifyToken(token):
            http_message = HttpMessage(is_success=False, data="Token无效")
            return http_message.getJson()
        # 获取列表
        beings_block_id = info["block_id"]
        if blockOfTimes.addTimesBlockQueue(beings_block_id):
            http_message = HttpMessage(is_success=True, data="推荐成功")
            return http_message.getJson()
        else:
            http_message = HttpMessage(is_success=False, data="该区块已经被推荐")
            return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@backstage.route("/backstage/beings/marker", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def markerBeings():
    """标记众生区块
        Content-Type: application/json
        {
          "token":"",
          "block_id":""
        }
        返回 json
        {
        "is_success":bool,
        "data":
        """
    try:
        info = request.get_json()
        # 验证token
        token = info["token"]
        if not auth.verifyToken(token):
            http_message = HttpMessage(is_success=False, data="Token无效")
            return http_message.getJson()
        # 获取列表
        beings_block_id = info["block_id"]
        if blockOfGarbage.addGarbageBlockQueue(beings_block_id):
            http_message = HttpMessage(is_success=True, data="标记成功")
            return http_message.getJson()
        else:
            http_message = HttpMessage(is_success=False, data="该区块已经被标记")
            return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@backstage.route("/backstage/beings/unmark", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def revocationBeings():
    """撤销标记众生区块
        Content-Type: application/json
        {
          "token":"",
          "block_id":""
        }
        返回 json
        {
        "is_success":bool,
        "data":
        """
    try:
        info = request.get_json()
        # 验证token
        token = info["token"]
        if not auth.verifyToken(token):
            http_message = HttpMessage(is_success=False, data="Token无效")
            return http_message.getJson()
        # 获取列表
        beings_block_id = info["block_id"]
        blockOfGarbage.revocationGarbageBlockQueueByBlockId(beings_block_id)
        http_message = HttpMessage(is_success=True, data="撤销标记成功")
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@backstage.route("/backstage/main_node/new_apply_list/get", methods=['POST'])
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


@backstage.route("/backstage/main_node/active_delete_list/get", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def getActiveDeleteList():
    """获取该主节点申请的已经广播的申请书列表（主动删除节点）
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
        res = mainNodeManager.getApplicationActiveDeleteListOfBroadcast(offset, count)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@backstage.route("/backstage/main_node/other_apply_list/get", methods=['POST'])
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


@backstage.route("/backstage/main_node/other_active_delete_list/get", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def getOtherActiveDeleteList():
    """获取其他主节点提交的申请书列表（主动删除）
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
        res = mainNodeManager.getApplicationActiveDeleteOfOtherMainNode(offset, count)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@backstage.route("/backstage/main_node/new_apply/get", methods=['POST'])
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


@backstage.route("/backstage/main_node/active_delete/get", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def getActiveDelete():
    """获取该主节点申请的已经广播的申请书（主动删除节点）
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
        res = mainNodeManager.getApplicationFormActiveDeleteByDBId(db_id)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@backstage.route("/backstage/main_node/active_delete/add", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def addActiveDelete():
    """主动申请删除谋主节点
    Content-Type: application/json
    {
      "token":"",
      "node_id":"",
      "application_content":"",
      "remarks":""
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
        node_id = info["node_id"]
        application_content = info["application_content"]
        remarks = info["remarks"]
        res = mainNodeManager.addApplicationFormActiveDelete(node_id, application_content, remarks)
        if res:
            http_message = HttpMessage(is_success=True, data="增加成功")
            return http_message.getJson()
        else:
            http_message = HttpMessage(is_success=False, data="增加失败")
            return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@backstage.route("/backstage/main_node/other_apply/get", methods=['POST'])
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


@backstage.route("/backstage/main_node/other_active_delete/get", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def getOtherActiveDelete():
    """获取其他主节点申请的已经广播的申请书（主动删除节点）
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
        res = mainNodeManager.getOtherNodeApplicationFormActiveDeleteByDBId(db_id)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@backstage.route("/backstage/main_node/new_apply/review", methods=['POST'])
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


@backstage.route("/backstage/main_node/other_apply/review", methods=['POST'])
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


@backstage.route("/backstage/main_node/other_active_delete/review", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def reviewOtherActiveDelete():
    """审核通过其他主节点的申请书（主动删除）
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
        mainNodeManager.reviewOtherNodeApplicationFormActiveDeleteByDBId(db_id, review)
        http_message = HttpMessage(is_success=True, data="审核完成")
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@backstage.route("/backstage/simple_user_vote/init", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def initSimpleUserVote():
    """初始化当前选举周期所有普通用户的票数
    Content-Type: application/json
    {
      "token":"",
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
        vote.initSimpleUserVote()
        http_message = HttpMessage(is_success=True, data="初始化完成")
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@backstage.route("/backstage/simple_user_vote_list/get", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def getSimpleUserVoteList():
    """获取普通用户票数列表
    Content-Type: application/json
    {
      "token":"",
      "offset":int,
      "count":int
    }
    返回 json
    {
    "is_success":bool,
    "data": ["user_pk"...]
    """
    try:
        info = request.get_json()
        # 验证token
        token = info["token"]
        if not auth.verifyToken(token):
            http_message = HttpMessage(is_success=False, data="Token无效")
            return http_message.getJson()
        offset = info["offset"]
        count = info["count"]
        res = vote.getListOfSimpleUserVote(offset, count)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@backstage.route("/backstage/simple_user_vote/get", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def getSimpleUserVote():
    """获取普通用户临时票票数
    Content-Type: application/json
    {
      "token":"",
      "user_pk":""
    }
    返回 json
    {
    "is_success":bool,
    "data": {}
    """
    try:
        info = request.get_json()
        user_pk = info["user_pk"]
        res = vote.getSimpleUserVoteByUserPk(user_pk)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@backstage.route("/backstage/simple_user_permanent_vote/get", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def getSimpleUserPermanentVote():
    """获取普通用户永久票票数
    Content-Type: application/json
    {
      "token":"",
      "user_pk":""
    }
    返回 json
    {
    "is_success":bool,
    "data": {}
    """
    try:
        info = request.get_json()
        user_pk = info["user_pk"]
        res = vote.getSimpleUserPermanentVoteByUserPk(user_pk)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@backstage.route("/backstage/simple_user_used_vote/add", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def addUsedVoteOfSimpleUser():
    """增加已使用的临时票票数
    Content-Type: application/json
    {
      "token":"",
      "user_pk":"",
      "used_vote":"",
    }
    返回 json
    {
    "is_success":bool,
    "data": {}
    """
    try:
        info = request.get_json()
        # 验证token
        token = info["token"]
        if not auth.verifyToken(token):
            http_message = HttpMessage(is_success=False, data="Token无效")
            return http_message.getJson()
        user_pk = info["user_pk"]
        used_vote = info["used_vote"]
        res = vote.addUsedVoteOfSimpleUser(user_pk, used_vote)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@backstage.route("/backstage/simple_user_vote/modify", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def modifyTotalVoteOfSimpleUser():
    """修改普通用户的总票数
    Content-Type: application/json
    {
      "token":"",
      "user_pk":"",
      "total_vote":""
    }
    返回 json
    {
    "is_success":bool,
    "data": {}
    """
    try:
        info = request.get_json()
        # 验证token
        token = info["token"]
        if not auth.verifyToken(token):
            http_message = HttpMessage(is_success=False, data="Token无效")
            return http_message.getJson()
        user_pk = info["user_pk"]
        total_vote = info["total_vote"]
        res = vote.modifyTotalVoteOfSimpleUser(user_pk, total_vote)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()
