from core.utils.ciphersuites import CipherSuites


class User:
    def __init__(self):
        self.__userSK = ""  # 密钥
        self.__userPK = ""  # 公钥

    # 设置用户密钥
    def setUserSK(self, sk):
        bytes_sk = bytes.fromhex(sk)
        self.__userSK = CipherSuites.getSKFromString(bytes_sk)

    # 生成用户密钥
    def generateUserSK(self):
        self.__userSK = CipherSuites.generateUserSK()

    # 获取用户密钥
    def getUserSK(self):
        return self.__userSK.to_string().hex()

    # 通过密钥生成公钥
    def generateUserVKBySK(self):
        self.__userPK = CipherSuites.SKtoVK(self.__userSK)

    # 新用户注册
    def register(self):
        self.generateUserSK()
        self.generateUserVKBySK()

    # 新用户登录
    def login(self, sk):
        self.setUserSK(sk)
        self.generateUserVKBySK()

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
    user.register()
    a = user.getUserPK().to_string()
    b = user.getUserPK().to_string().hex()
    c = bytes.fromhex(b)
    print(c)
