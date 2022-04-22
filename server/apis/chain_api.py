import traceback
from flask import request, Blueprint
from flask_cors import cross_origin
from server.utils.message import HttpMessage
from server.utils.ciphersuites import CipherSuites
from server.config import Allow_Url_List
from server.apis.api_init import auth, blockOfBeings, blockOfTimes, blockOfGarbage, mainNodeManager, vote, chainOfBlock, \
    chainOfTimes, chainOfGarbage

chain = Blueprint('chain', __name__)


@chain.route('/period/get', methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getPeriod():
    """
    获取众生区块生成期次和选举期次
    :return:
    {
    "is_success":bool,
    "data":
        {
        "epoch":int
        "election_period":int
        }
    }
    """
    try:
        data = mainNodeManager.getEpochAndElectionPeriod()
        http_message = HttpMessage(is_success=True, data=data)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data=err)
        return http_message.getJson()


@chain.route('/block/beings/save', methods=['POST'])
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
        }
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
@chain.route("/captcha/get", methods=['POST'])
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


@chain.route("/main_node/new_apply/save", methods=['POST'])
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


@chain.route("/chain/beings/get", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getBeingsOfChain():
    """获取众生链区块
   Content-Type: application/json
   {
     ?block_id=sfsdfdfnsdjfnsdjfnsdjgsdjg
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
        block_id = request.args.get("block_id")
        block_dict = chainOfBlock.getBlockByBlockId(block_id)
        http_message = HttpMessage(is_success=True, data=block_dict)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@chain.route("/chain/beings_list/get", methods=['GET'])
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


@chain.route("/chain/beings_list/offset_get", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getBeingsListOfChainByOffset():
    """获取众生链区块ID列表(倒序偏移获取）
   {
     ?offset=128&count=8
   }
   返回 json
   {
   "is_success":bool,
   "data": [id...]
   """
    try:
        offset = int(request.args.get("offset"))
        count = int(request.args.get("count"))
        if count > 8:
            http_message = HttpMessage(is_success=False, data="每次最多获取8个Epoch的区块")
            return http_message.getJson()
        id_list = chainOfBlock.getIDListOfBlockByOffset(offset, count)
        http_message = HttpMessage(is_success=True, data=id_list)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@chain.route("/chain/beings/epoch_list", methods=['GET'])
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
        offset = int(request.args.get("offset"))
        count = int(request.args.get("count"))
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


@chain.route("/chain/beings/max_epoch", methods=['GET'])
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


@chain.route("/chain/times_list/get", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getTimesListOfChain():
    """获取时代链区块列表
   {
     ?offset=0&count=8
   }
   返回 json
   {
   "is_success":bool,
   "data": [{}，{}。。。。]
   """
    try:
        offset = int(request.args.get("offset"))
        count = int(request.args.get("count"))
        if count > 8:
            http_message = HttpMessage(is_success=False, data="每次最多查询8个选举周期的区块")
            return http_message.getJson()
        times_list = chainOfTimes.getListOfTimesByOffset(offset, count)
        http_message = HttpMessage(is_success=True, data=times_list)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@chain.route("/chain/times_list/get_by_election_period", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getTimesListOfChainByElectionPeriod():
    """获取时代链区块列表
   {
     ?start=0&end=8
   }
   返回 json
   {
   "is_success":bool,
   "data": [{}，{}。。。。]
   """
    try:
        start = int(request.args.get("start"))
        end = int(request.args.get("end"))
        if end - start > 8:
            http_message = HttpMessage(is_success=False, data="每次最多查询8个选举周期的区块")
            return http_message.getJson()
        times_list = chainOfTimes.getListOfBlockByElectionPeriod(start, end)
        http_message = HttpMessage(is_success=True, data=times_list)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@chain.route("/chain/garbage_list/get", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getGarbageListOfChain():
    """获取垃圾链区块列表
   {
     ?offset=0&count=8
   }
   返回 json
   {
   "is_success":bool,
   "data": [{}，{}。。。。]
   """
    try:
        offset = int(request.args.get("offset"))
        count = int(request.args.get("count"))
        if count > 8:
            http_message = HttpMessage(is_success=False, data="每次最多查询8个选举周期的垃圾区块")
            return http_message.getJson()
        garbage_list = chainOfGarbage.getListOfGarbageByOffset(offset, count)
        http_message = HttpMessage(is_success=True, data=garbage_list)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@chain.route("/chain/garbage_list/get_by_election_period", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getGarbageListOfChainByElectionPeriod():
    """获取垃圾链区块列表
   {
     ?start=0&end=8
   }
   返回 json
   {
   "is_success":bool,
   "data": [{}，{}。。。。]
   """
    try:
        start = int(request.args.get("start"))
        end = int(request.args.get("end"))
        if end - start > 8:
            http_message = HttpMessage(is_success=False, data="每次最多查询8个选举周期的区块")
            return http_message.getJson()
        garbage_list = chainOfGarbage.getListOfBlockByElectionPeriod(start, end)
        http_message = HttpMessage(is_success=True, data=garbage_list)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@chain.route("/times_block_list/get", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getListOfTimesBlockQueue():
    """获取正在推荐的众生区块列表(倒序偏移获取）
    {
     ?election_period=0&offset=0&count=8
   }
   返回 json
   {
   "is_success":bool,
   "data": [{id,election_period,beings_block_id,votes}]
   """
    try:
        election_period = int(request.args.get("election_period"))
        offset = int(request.args.get("offset"))
        count = int(request.args.get("count"))
        if count > 32:
            http_message = HttpMessage(is_success=False, data="每次最多获取32个众生区块ID信息")
            return http_message.getJson()
        res = blockOfTimes.getListOfTimesBlockQueue(offset, count, election_period)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@chain.route("/times_block/get", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getTimesBlock():
    """获取正在推荐的众生区块
    {
     ?block_id=
   }
   返回 json
   {
   "is_success":bool,
   "data": {"id": ,
            "election_period":
            "beings_block_id":
            "votes":
            "vote_list":
            "status":
            "create_time":
   """
    try:
        beings_block_id = request.args.get("block_id")
        res = blockOfTimes.getTimesBlockQueue(beings_block_id)
        if res is None:
            http_message = HttpMessage(is_success=False, data=res)
        else:
            http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@chain.route("/garbage_block_list/get", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getListOfGarbageBlockQueue():
    """获取正在标记的众生区块列表(倒序偏移获取）
    {
     ?election_period=0&offset=0&count=8
   }
   返回 json
   {
   "is_success":bool,
   "data": [{id,election_period,beings_block_id,votes}]
   """
    try:
        election_period = int(request.args.get("election_period"))
        offset = int(request.args.get("offset"))
        count = int(request.args.get("count"))
        if count > 32:
            http_message = HttpMessage(is_success=False, data="每次最多获取32个众生区块ID信息")
            return http_message.getJson()
        res = blockOfGarbage.getListOfGarbageBlockQueue(offset, count, election_period)
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@chain.route("/garbage_block/get", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getGarbageBlock():
    """获取正在标记的众生区块
    {
     ?block_id=
   }
   返回 json
   {
   "is_success":bool,
   "data": {"id": ,
            "election_period":
            "beings_block_id":
            "votes":
            "vote_list":
            "status":
            "create_time":
   """
    try:
        beings_block_id = request.args.get("block_id")
        res = blockOfGarbage.getGarbageBlockQueue(beings_block_id)
        if res is None:
            http_message = HttpMessage(is_success=False, data=res)
        else:
            http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@chain.route("/vote_list/main_node/get", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getVoteListOfMainNode():
    """获取所有主节点的票数列表
   返回 json
   {
   "is_success":bool,
   "data": [{node_id,node_user_Pk},。。。]
   }
   """
    try:
        res = vote.getListOfMainNodeVote()
        http_message = HttpMessage(is_success=True, data=res)
        return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@chain.route("/vote/main_node/get", methods=['GET'])
@cross_origin(origins=Allow_Url_List)
def getVoteOfMainNode():
    """获取主节点的票数信息
    {
    ?user_pk=
    }
   返回 json
   {
   "is_success":bool,
   "data": {"id": ,
            "main_node_id": ,
            "main_node_user_pk":,
            "total_vote": ,
            "used_vote":,
            "update_time": ,
            "create_time": }
   }
   """
    try:
        user_pk = request.args.get("user_pk")
        res = vote.getMainNodeVoteByMainNodeUserPk(main_node_user_pk=user_pk)
        if res is not None:
            http_message = HttpMessage(is_success=True, data=res)
            return http_message.getJson()
        else:
            http_message = HttpMessage(is_success=False, data=None)
            return http_message.getJson()
    except Exception as err:
        print(err)
        http_message = HttpMessage(is_success=False, data="参数错误")
        return http_message.getJson()


@chain.route("/vote/add", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def initiateVoting():
    """发起临时票投票
    {
    "captcha“：{},
    ”to_node_id“：”“,
    ”block_id“：”“,
    ”to_vote“：”“,
    ”simple_user_pk“：”“,
    "signature“：”“,
    }
   返回 json
   {
   "is_success":bool,
   "data": {}
   }
   """
    if request.method == 'POST':
        info = request.get_json()
        try:
            captcha = info["captcha"]
            if not auth.verifyCaptcha(uuid=captcha["uuid"], word=captcha["word"]):
                http_message = HttpMessage(is_success=False, data="验证码错误")
                return http_message.getJson()
            to_node_id = info["to_node_id"]
            block_id = info["block_id"]
            to_vote = info["to_vote"]
            simple_user_pk = info["simple_user_pk"]
            signature = info["signature"]
            is_success = vote.initiateVoting(to_node_id=to_node_id, block_id=block_id, vote=to_vote,
                                             simple_user_pk=simple_user_pk, signature=signature)
            if is_success:
                http_message = HttpMessage(is_success=True, data="投票成功")
                return http_message.getJson()
            else:
                http_message = HttpMessage(is_success=False, data="投票失败")
                return http_message.getJson()
        except Exception as err:
            traceback.print_exc()
            http_message = HttpMessage(is_success=False, data="参数错误")
            return http_message.getJson()


@chain.route("/permanent_vote/add", methods=['POST'])
@cross_origin(origins=Allow_Url_List)
def initiatePermanentVoting():
    """发起长期票投票
    {
    "captcha“：{},
    ”to_node_id“：”“,
    ”block_id“：”“,
    ”to_vote“：”“,
    ”simple_user_pk“：”“,
    "signature“：”“,
    }
   返回 json
   {
   "is_success":bool,
   "data": {}
   }
   """
    if request.method == 'POST':
        info = request.get_json()
        try:
            captcha = info["captcha"]
            if not auth.verifyCaptcha(uuid=captcha["uuid"], word=captcha["word"]):
                http_message = HttpMessage(is_success=False, data="验证码错误")
                return http_message.getJson()
            to_node_id = info["to_node_id"]
            block_id = info["block_id"]
            to_vote = info["to_vote"]
            simple_user_pk = info["simple_user_pk"]
            signature = info["signature"]
            is_success = vote.initiatePermanentVoting(to_node_id=to_node_id, block_id=block_id, vote=to_vote,
                                                      simple_user_pk=simple_user_pk, signature=signature)
            if is_success:
                http_message = HttpMessage(is_success=True, data="投票成功")
                return http_message.getJson()
            else:
                http_message = HttpMessage(is_success=False, data="投票失败")
                return http_message.getJson()
        except Exception as err:
            traceback.print_exc()
            http_message = HttpMessage(is_success=False, data="参数错误")
            return http_message.getJson()
