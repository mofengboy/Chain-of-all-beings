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
        seed = hashlib.sha256(block_abstract + str(epoch))
        return seed


if __name__ == "__main__":
    pk = "8778e91df26e1510781783925e51c8af2719e768b402b1a2ecc0d18965f1701abe96424d6c48095fbb96ed6ba1f0c9213c858a702c4786c5cea2e23c463a70d52d74a3c717e74fecb8d2933a3a6961ad296bda8e07f091decd2a2f83aaaad4fa"
    a = str("abc").encode()
    sig = '69f6305455a23f9195092b0e1d8cd4ba18b6165f95e42a65421d0c0a7baff29d0db55c559e4bd327e49c9a361c23c92cabc7851bde166243135e6df60d473ba69bd33671ace3434d174d22ed1691d852ea5ada4ae9b59cf6b3e598121c2f11a2'
    fl = CipherSuites.verify(pk, bytes.fromhex(sig), a)
    print(fl)
