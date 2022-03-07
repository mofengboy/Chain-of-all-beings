import hashlib

from ecdsa import SigningKey, NIST384p, VerifyingKey


class CipherSuites:
    # 验证签名
    @staticmethod
    def verify(pk, signature, message: bytes) -> bool:
        vk = VerifyingKey.from_string(bytes.fromhex(pk), curve=NIST384p, hashfunc=hashlib.sha256)
        return vk.verify(bytes.fromhex(signature), message)
