import logging
import base64

from core.utils.ciphersuites import CipherSuites

logger = logging.getLogger("main")


class User:
    def __init__(self):
        self.__userSK = ""  # 密钥
        self.__userPK = ""  # 公钥

    # 设置用户密钥
    def setUserSK(self, sk_string):
        bytes_sk = bytes.fromhex(sk_string)
        self.__userSK = CipherSuites.getSKFromString(bytes_sk)

    # 设置用户公钥
    def setUserPK(self, pk_string):
        bytes_pk = bytes.fromhex(pk_string)
        self.__userPK = CipherSuites.getPKFromString(bytes_pk)

    # 生成用户密钥
    def generateUserSK(self):
        self.__userSK = CipherSuites.generateUserSK()

    # 获取用户密钥
    def getUserSKString(self):
        return self.__userSK.to_string().hex()

    # 通过密钥生成公钥
    def generateUserVKBySK(self):
        self.__userPK = CipherSuites.SKtoVK(self.__userSK)

    # 新用户注册
    def register(self):
        self.generateUserSK()
        self.generateUserVKBySK()
        print("-" * 32)
        print("私钥")
        print(self.getUserSKString())
        print("公钥")
        print(self.getUserPKString())
        print("-" * 32)
        logger.info("用户已经注册")
        logger.info("公钥为：" + self.getUserPKString())

    # 新用户登录
    def login(self, sk_string, pk_string):
        # 验证私钥和公钥是否匹配
        if not CipherSuites.verifyPublicAndPrivateKeys(sk_string, pk_string):
            logger.warning("私钥与公钥不匹配！")
            exit()
        self.setUserSK(sk_string)
        self.setUserPK(pk_string)
        logger.info("用户已经登录")
        logger.info("公钥为：" + self.getUserPKString())

    def getUserPK(self):
        return self.__userPK

    def getUserPKString(self):
        return self.__userPK.to_string().hex()

    # 签名
    def sign(self, message: bytes):
        signature = CipherSuites.sign(self.__userSK, message)
        return signature.hex()


if __name__ == "__main__":
    user = User()
    # for i in range(5):
    #     user.register()
    #     user_pk = user
    #     print(user_pk)
    #     print(len(user_pk))
    body = "# markdown文件格式".encode("utf-8")
    # body = base64.b64encode(body)
    # a = user.sign(message=body)
    # print(a)
    user.register()
    a_list = []
    for i in range(5):
        a = user.sign(message=body)
        print(a)
        print(len(a))
        a_list.append(a)
    #
    for i in a_list:
        print(CipherSuites.verify(pk=user.getUserPKString(), signature=i, message=body))
    # pk = "d0644eb8b673de6bccad286ba4703476bb9a8498772ce9592476a5556a47bb5da4b28744b7774e49efda62eaf7d92b98f7b0f0c03b2d33418305f94e77e78026e2506a0926f23e7d09be6deadd6a87a029ea86e0e8187b9f9c1301060bf0921a"
    # mes = "IyBtYXJrZG93buaWh+S7tuagvOW8jw==".encode("utf-8")
    # sig = '4a877320a8603ffa9050f2a21f03a3209b327a66b4eb9609da1a7b7e5d1376a81b9f0cc3507f8364818bfd38785f441b6904ba9449e44c51e6390f985ca9f40390df0b12160a121072b3c9f360ca83da9175ef3ba625f8b852aa065771bb558f'
    # a = CipherSuites.verify(pk=pk, signature=sig, message=mes)
    # print(a)
