import time

from server.utils.captcha import Captcha
from server.utils.ciphersuites import CipherSuites
from server.utils.core_sdk import DBOfTemp, DBOfBlock, VoteOfMainNode
from server.database import DB
import hashlib

Valid_Time = 1800  # 30分钟


# 权限验证
class Auth:
    def __init__(self, db: DB):
        self.__tokens = []
        self.captcha = Captcha()
        self.db = db

    # 验证用户名和密码并获取token
    def generateTokenByUsernameAndPassword(self, username, password):
        password_abstract = hashlib.sha256(str(password).encode("utf-8")).hexdigest()
        # 数据库比对
        if self.db.verifyUsernameAndPassword(username=username, password=password_abstract):
            token = hashlib.sha256(str(username + password_abstract + (str(time.time()))).encode("utf-8")).hexdigest()[
                    0:64]
            # 清楚重复token
            i = 0
            for token_i in self.__tokens:
                if token_i["username"] == username:
                    del self.__tokens[i]
                i += 1
            # 生成 token 保存在内存中
            self.__tokens.append({
                "username": username,
                "token": token,
                'time': time.time()
            })
            return token
        else:
            return "false"

    def verifyToken(self, token) -> bool:
        # 清除过期token
        for i in range(len(self.__tokens)):
            if time.time() - self.__tokens[i]["time"] > Valid_Time:
                del self.__tokens[i]

        # 比对token
        for token_i in self.__tokens:
            if token_i["token"] == token:
                # 更新有效时间
                token_i["time"] = time.time()
                return True
        return False

    # 获取验证码
    def getCaptcha(self):
        uuid, pic_base64 = self.captcha.generate()
        return {
            "uuid": uuid,
            "pic_base64": pic_base64
        }

    # 验证验证码
    def verifyCaptcha(self, uuid, word) -> bool:
        return self.captcha.verify(uuid=uuid, word=word)


class BackStageInfo:
    def __init__(self, db: DB):
        self.backstageDB = db

    # 获取首页通知
    def getIndexNotice(self):
        return self.backstageDB.getIndexNotice()

    # 修改首页通知
    def modifyIndexNotice(self, content):
        return self.backstageDB.modifyIndexNotice(content)

    # 获取备案号
    def getRecordNumber(self):
        return self.backstageDB.getRecordNumber()

    # 设置备案号
    def setRecordNumber(self, record_number):
        return self.backstageDB.setRecordNumber(record_number)


# 众生区块（待发布）
class BlockOfBeings:
    def __init__(self, db: DB):
        self.db = db

    def addBlock(self, user_pk, body: str, signature) -> bool:
        body = str(body).encode("utf-8")
        try:
            # 验证签名
            if not CipherSuites.verify(pk=user_pk, message=body, signature=signature):
                return False
            # 存储
            self.db.insertBlockOfBeings(user_pk=user_pk, body=body, signature=signature)
            return True
        except Exception as err:
            print(err)
            return False

    def getBlockList(self, offset=None, count=1):
        if offset is None:
            id_list = self.db.getBlockListOfBeings(count)
            return id_list
        else:
            id_list = self.db.getBlockListOfBeingsByOffset(offset, count)
            return id_list

    def getWaitingBlockList(self, offset, count):
        id_list = self.db.getWaitingBlockListOfBeingsByOffset(offset, count)
        return id_list

    def getBlockByDBId(self, db_id):
        block = self.db.getBlockOfBeingsByDBId(db_id=db_id)
        return block

    def reviewBlock(self, db_id, is_review):
        self.db.reviewBlockOfBeingsDBId(db_id=db_id, is_review=is_review)


# 时代区块（待发布）
class BlockOfTimes:
    def __init__(self, db: DB):
        self.db = db
        self.DBOfTemp = DBOfTemp()

    # 推荐众生区块
    def addTimesBlockQueue(self, beings_block_id):
        election_period = self.DBOfTemp.getElectionPeriod()
        return self.db.insertTimesBlockQueue(election_period, beings_block_id, 0, [])

    # 撤销推荐众生区块
    def revocationTimesBlockQueueByBlockId(self, beings_block_id):
        self.db.modifyStatusOfTimesBlockQueue(beings_block_id, 2)

    def getListOfTimesBlockQueue(self, offset, count, election_period):
        data = self.db.getListOfTimesBlockQueue(offset, count, election_period)
        return data

    def getTimesBlockQueue(self, beings_block_id):
        data = self.db.getTimesBlockQueue(beings_block_id)
        return data


# 众生链（已经发布的区块）
class ChainOfBeings:
    def __init__(self):
        self.dbOfBeings = DBOfBlock()

    def getIDListOfBlockByEpoch(self, start, end):
        id_list = self.dbOfBeings.getIDListOfBeingsByEpoch(start, end)
        return id_list

    def getIDListOfBlockByOffset(self, offset, count):
        id_list = self.dbOfBeings.getIDListOfBeingsByOffset(offset, count)
        return id_list

    def getEpochLIst(self, offset, count):
        return self.dbOfBeings.getEpochList(offset, count)

    def getBlockByBlockId(self, block_id):
        block_dict = self.dbOfBeings.getBlockOfBeingsByBlockId(block_id)
        return block_dict

    def getMaxEpoch(self):
        return self.dbOfBeings.getMaxEpoch()


class MainNodeManager:
    def __init__(self, db: DB):
        self.DBOfTemp = DBOfTemp()
        self.db = db

    # 获取该主节点接受到的等待审核的申请表列表id
    def getApplicationListOfMainNode(self, offset, count):
        id_list = self.db.getApplicationFormByOffset(offset, count)
        return id_list

    # 获取申请表
    def getApplicationFormByDBId(self, db_id):
        application_form_dict = self.db.getApplicationFormByDBId(db_id)
        return application_form_dict

    # 审核申请表
    def reviewApplicationFormByDBId(self, db_id, is_review):
        self.db.reviewApplicationFormByDBId(db_id, is_review)

    # 增加申请表列表
    def addApplicationForm(self, node_id, user_pk, node_ip, server_url, node_create_time, node_signature, application,
                           application_signature, remarks) -> bool:
        # 验证签名
        # 验证新节点信息和签名
        node_info = "{'node_id': '" + node_id + "', 'user_pk': '" + user_pk + "', 'node_ip': '" + node_ip + "', 'server_url': '" + server_url + "', 'create_time': " + node_create_time + "}"
        if not CipherSuites.verify(pk=user_pk, signature=node_signature,
                                   message=str(node_info).encode("utf-8")):
            # 新节点信息与签名不匹配
            return False
        # 验证申请书和签名
        if not CipherSuites.verify(pk=user_pk, signature=application_signature,
                                   message=str(application).encode("utf-8")):
            # 申请书与新节点签名不匹配
            return False
        self.db.insertApplicationForm(node_id, user_pk, node_ip, server_url, node_create_time, node_signature,
                                      application, application_signature, remarks)
        return True

    # 获取从其他主节点接受到的等待审核的申请表列表id
    def getApplicationOfOtherMainNode(self, offset, count):
        id_list = self.DBOfTemp.getListOfWaitingApplicationForm(offset, count)
        return id_list

    # 获取从其他主节点接受到的等待审核的申请表
    def getOtherNodeApplicationFormByDBId(self, db_id):
        application_form = self.DBOfTemp.getWaitingApplicationForm(db_id)
        return application_form

    # 审核从其他主节点接受到的等待审核的申请表
    def reviewOtherNodeApplicationFormByDBId(self, db_id, is_audit):
        self.DBOfTemp.auditWaitingApplicationForm(db_id, is_audit)

    def getEpochAndElectionPeriod(self):
        epoch = self.DBOfTemp.getEpoch()
        electionPeriodValue = self.DBOfTemp.getElectionPeriodValue()
        return {
            "epoch": epoch,
            "election_period_value": electionPeriodValue
        }


class Vote:
    def __init__(self, db: DB):
        self.voteOfMainNode = VoteOfMainNode()
        self.dbOfBlock = DBOfBlock()
        self.dbOfTemp = DBOfTemp()
        self.db = db

    # 获取所有主节点的投票信息列表
    def getListOfMainNodeVote(self):
        return self.voteOfMainNode.getListOfMainNodeVote()

    # 获取主节点的投票信息
    def getMainNodeVoteByMainNodeUserPk(self, main_node_user_pk):
        return self.voteOfMainNode.getMainNodeVoteByMainNodeUserPk(main_node_user_pk=main_node_user_pk)

    # 初始化普通用户的票数信息
    def initSimpleUserVote(self):
        election_period_value = self.voteOfMainNode.getElectionPeriodValue()
        current_election_period = int(self.dbOfTemp.getEpoch() / election_period_value)
        start_election_period = current_election_period - 8
        main_node_user_pk = self.dbOfTemp.getNodeInfo().userPk
        list_of_all_simple_user = {}
        for i in range(start_election_period, current_election_period):
            list_of_simple_user = self.dbOfBlock.getListOfSimpleUser(main_node_user_pk=main_node_user_pk,
                                                                     start_epoch=i * election_period_value,
                                                                     end_epoch=(i + 1) * election_period_value)
            for simple_user_pk in list_of_simple_user.keys():
                if simple_user_pk in list_of_all_simple_user.keys():
                    list_of_all_simple_user[simple_user_pk] += list_of_simple_user[simple_user_pk]
                else:
                    list_of_all_simple_user[simple_user_pk] = list_of_simple_user[simple_user_pk]
        # 清除数据
        self.db.clearSimpleUserVote()
        # 增加数据
        for user_pk in list_of_all_simple_user.keys():
            self.db.addSimpleUserVote(election_period=current_election_period, user_pk=user_pk,
                                      total_vote=float(list_of_all_simple_user[user_pk]))

    # 获取普通用户的票数信息列表 公钥列表
    def getListOfSimpleUserVote(self, offset, count):
        return self.db.getListOfSimpleUserVote(offset, count)

    # 获取普通用户的票数信息
    def getSimpleUserVoteByUserPk(self, user_pk):
        return self.db.getSimpleUserVoteByUserPk(user_pk)

    # 增加已使用的票数
    def addUsedVoteOfSimpleUser(self, user_pk, used_vote):
        return self.db.addUsedVoteOfSimpleUser(user_pk, used_vote)

    # 修改普通用户的总票数
    # 修改后的总票数不能低于已经使用的票数
    # 修改后的总票数不能高于当前主节点剩余的票数
    def modifyTotalVoteOfSimpleUser(self, user_pk, total_vote):
        main_node_user_pk = self.dbOfTemp.getNodeInfo().userPk
        res_data = self.getMainNodeVoteByMainNodeUserPk(main_node_user_pk)
        if res_data is None:
            return False
        main_node_total_vote = res_data["total_vote"]
        main_node_used_vote = res_data["used_vote"]
        if total_vote > (main_node_total_vote - main_node_used_vote):
            return False
        return self.db.modifyTotalVoteOfSimpleUser(user_pk, total_vote)

    # 发起投票
    def initiateVoting(self, to_node_id, block_id, vote, simple_user_pk, signature) -> bool:
        if vote < 1.0:
            return False
        simple_user_vote = self.getSimpleUserVoteByUserPk(simple_user_pk)
        if (simple_user_vote["total_vote"] - simple_user_vote["used_vote"]) < vote:
            return False
        # 验证签名
        election_period_value = self.voteOfMainNode.getElectionPeriodValue()
        current_election_period = int(self.dbOfTemp.getEpoch() / election_period_value)
        vote_info = "{'election_period': " + str(
            current_election_period) + ", 'to_node_id': " + to_node_id + ", 'block_id': " + block_id + ", 'vote': " + vote + ", 'simple_user_pk': " + simple_user_pk + "}"
        try:
            if not CipherSuites.verify(pk=simple_user_pk, signature=signature, message=str(vote_info).encode("utf-8")):
                return False
        except Exception as err:
            print(err)
            return False
        self.addUsedVoteOfSimpleUser(user_pk=simple_user_vote, used_vote=vote)
        election_period_value = self.voteOfMainNode.getElectionPeriodValue()
        current_election_period = int(self.dbOfTemp.getEpoch() / election_period_value)
        self.dbOfTemp.addVoteMessage(election_period=current_election_period, to_node_id=to_node_id,
                                     block_id=block_id, vote=vote, simple_user_pk=simple_user_pk, signature=signature)
        return True
