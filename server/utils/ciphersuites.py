import hashlib

from ecdsa import SigningKey, NIST384p, VerifyingKey


class CipherSuites:
    # 验证签名
    @staticmethod
    def verify(pk, signature, message: bytes) -> bool:
        vk = VerifyingKey.from_string(bytes.fromhex(pk), curve=NIST384p, hashfunc=hashlib.sha256)
        return vk.verify(bytes.fromhex(signature), message)


if __name__ == "__main__":
    a = "{'node_id': 'dad4f7979931824c', 'user_pk': 'dad4f7979931824ccd6a6ae3bdb439b8aea267a62f188cbafd54f6f85d2eb68f566a12cedaed974beb070af80f3cc7178546c3b9a4def8364de07a0ff1bcacaa226867d4c20920c726233b24a399fcac024671076415e67b0d708ac1fdfc8fa3', 'node_ip': '103.97.201.117', 'create_time': 1647347417275}"
    publicKey = "dad4f7979931824ccd6a6ae3bdb439b8aea267a62f188cbafd54f6f85d2eb68f566a12cedaed974beb070af80f3cc7178546c3b9a4def8364de07a0ff1bcacaa226867d4c20920c726233b24a399fcac024671076415e67b0d708ac1fdfc8fa3"
    nodeSignatureRaw = "f6a6c3c5144f030df2ad45ec436f9153fad7dbc5c444d86983e02a41a1e013ac51540921045a1edc7e024cb28da82b78a87ced7af6ac598a3b9a0fe6ceeae75315ae556b681e4d15b31ea808022d8e1078c5eecacc6f27c1371475eebfc488f9"
    b = CipherSuites.verify(pk=publicKey, signature=nodeSignatureRaw, message=str(a).encode("utf-8"))
    print(b)
