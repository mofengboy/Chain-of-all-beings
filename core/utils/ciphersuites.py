from ecdsa import SigningKey, NIST384p, VerifyingKey
import hashlib
import time
import random

from core.utils.system_time import STime


class CipherSuites:

    # 生成区块ID
    @staticmethod
    def generateBlockID(e, block_type, user_pk):
        tail = hashlib.md5((str(e) + str(user_pk)).encode("utf-8")).hexdigest()[0:8]
        block_id = block_type + "e" + str(e) + "z" + tail  # 区块ID 构成:类型+e+轮次+z+mad5(轮次+用户公钥）
        return block_id

    # 生成用户私钥（签名密钥）
    @staticmethod
    def generateUserSK():
        sk = SigningKey.generate(curve=NIST384p)
        return sk

    @staticmethod
    def getSKFromString(string):
        return SigningKey.from_string(string)

    # 由用户私钥（签名密钥）得到用户公钥（验证公钥）
    @staticmethod
    def SKtoVK(sk):
        return sk.verifying_key

    # 对消息进行签名
    @staticmethod
    def sign(sk, message):
        return sk.sign(message)

    # 验证签名
    @staticmethod
    def verify(pk, signature, message: bytes) -> bool:
        vk = VerifyingKey.from_string(bytes.fromhex(pk), curve=NIST384p)
        return vk.verify(bytes.fromhex(signature), message)

    # 生成区块值哈希
    @staticmethod
    def generateSHA256(string):
        return hashlib.sha256(string)

    @staticmethod
    def getSeed(block_abstract, epoch):
        seed = hashlib.sha256((block_abstract + str(epoch)).encode("utf-8"))
        return seed


if __name__ == "__main__":
    pk = "04e9d2202827c544266b7ce7bfc1f43b4eff15afc9f713371ad367ee4ad2df0e881f1657b516f15df8c195c1c8bc29dbfcb6a37ab3eb4e3e3deeeef5e1f9711de13a1571566d63361518d382d22a014db3cdbebf8b0f3ccefcfd359fbb2ea0c81e"
    a = str("d04b98f48e8f8bcc15c6ae5ac050801cd6dcfd428fb5f9e65c4e16e7807340fa").encode()
    sig = "5367c5743591b5573a65cfe2f31fd2010b051dddc8d48c53f0601071dcd47fec139c98881f5255ea8607837e10a3a8abee0fc96b2eed998ac4b1cb1263b46bc468f04dbdfa79aedd6c70906f25a4fb0484d3375542558eca262f21be0e36db61"
    fl = CipherSuites.verify(pk=pk, signature=sig, message=a)
    print(fl)
