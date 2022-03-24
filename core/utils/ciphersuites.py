from ecdsa import SigningKey, NIST384p, VerifyingKey
import hashlib
import random

from core.data.node_info import NodeInfo


class CipherSuites:

    # 生成区块ID
    @staticmethod
    def generateBlockID(e, block_type, user_pk):
        tail = hashlib.sha256((str(e) + str(user_pk)).encode("utf-8")).hexdigest()[0:32]
        block_id = block_type + "e" + str(e) + "z" + tail  # 区块ID 构成:类型+e+轮次+z+mad5(轮次+用户公钥）
        return block_id

    # 生成用户私钥（签名密钥）
    @staticmethod
    def generateUserSK():
        sk = SigningKey.generate(curve=NIST384p, hashfunc=hashlib.sha256)
        return sk

    @staticmethod
    def getSKFromString(string_bytes: bytes) -> SigningKey:
        return SigningKey.from_string(string_bytes, curve=NIST384p)

    @staticmethod
    def getPKFromString(string_bytes: bytes) -> VerifyingKey:
        return VerifyingKey.from_string(string_bytes, curve=NIST384p)

    # 由用户私钥（签名密钥）得到用户公钥（验证公钥）
    @staticmethod
    def SKtoVK(sk):
        return sk.verifying_key

    # 对消息进行签名
    @staticmethod
    def sign(sk, message):
        return sk.sign(message, hashfunc=hashlib.sha256)

    # 验证签名
    @staticmethod
    def verify(pk, signature, message: bytes) -> bool:
        vk = VerifyingKey.from_string(bytes.fromhex(pk), curve=NIST384p, hashfunc=hashlib.sha256)
        return vk.verify(bytes.fromhex(signature), message)

    # 生成区块值哈希
    @staticmethod
    def generateSHA256(string):
        return hashlib.sha256(string)

    @staticmethod
    def getSeed(block_abstract, epoch):
        seed = hashlib.sha256((block_abstract + str(epoch)).encode("utf-8"))
        return seed

    # 验证公钥和私钥是否匹配
    @staticmethod
    def verifyPublicAndPrivateKeys(sk_string, pk_string):
        sk = CipherSuites.getSKFromString(bytes.fromhex(sk_string))
        content = random.random()
        signature = CipherSuites.sign(sk, str(content).encode("utf-8")).hex()
        return CipherSuites.verify(pk=pk_string, signature=signature, message=str(content).encode("utf-8"))


if __name__ == "__main__":
    node_info = NodeInfo(node_id="495c3283c77f7ef2",
                         user_pk="495c3283c77f7ef207a35895452eb0ded704b44ab67bfd6aafb0959d6ffc2887b838305da9fcf06caa0c4f61e741364d5d15bd84a68604653119a908c76322c2b67926ef4b52ea51543499c6259542774605082fc12d4ac3b0f29cd7a70db54f",
                         node_ip="111.14.210.81", create_time=1648045205157)
    a = CipherSuites.verify(
        pk="495c3283c77f7ef207a35895452eb0ded704b44ab67bfd6aafb0959d6ffc2887b838305da9fcf06caa0c4f61e741364d5d15bd84a68604653119a908c76322c2b67926ef4b52ea51543499c6259542774605082fc12d4ac3b0f29cd7a70db54f",
        signature="c87469e23caef553b82d8aa90e2de9e3d40b5b8c00ff4804f9f31fee2234b4564ebedde5385ab0683698ac563037e36642ecb35be775b3e67749928366e794eefbcba7225b5a50917e2e24fc8090ecc61350652380341421b8596ef378aaf59c",
        message=str(node_info.getInfo()).encode("utf-8"))
    print(a)
