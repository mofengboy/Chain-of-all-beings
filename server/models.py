import time

from server.utils.captcha import Captcha
from server.utils.ciphersuites import CipherSuites
from server.utils.core_sdk import DBOfTemp, DBOfBlock
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


# 众生链（已经发布的区块）
class ChainOfBeings:
    def __init__(self):
        self.dbOfBeings = DBOfBlock()

    def getIDListOfBlockByEpoch(self, start, end):
        id_list = self.dbOfBeings.getIDListOfBeingsByEpoch(start, end)
        return id_list

    def getBlockByID(self, db_id):
        block_dict = self.dbOfBeings.getBlockOfBeings(db_id)
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
