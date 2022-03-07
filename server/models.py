import time

from server.utils.captcha import Captcha
from server.utils.ciphersuites import CipherSuites
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
