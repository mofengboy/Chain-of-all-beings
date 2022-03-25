from core.consensus.block_generate import NewBlockOfBeingsByExist
from core.data.block_of_beings import BlockOfBeings
from core.utils.ciphersuites import CipherSuites


# 创世区块
class GenesisBlock:
    def __init__(self):
        genesis_pre_block_header = ["0" * 64]
        genesis_pre_block = ["0" * 64]
        genesis_body = str(
            "IyDliJvkuJbljLrlnZcKCuaxn+eVlOS9leS6uuWIneingeaciD8g5rGf5pyI5L2V5bm05Yid54Wn5Lq6PyDkurrnlJ/ku6Pku6Pml6Dnqbflt7IsIOaxn+aciOW5tOW5tOWPquebuOS8vC4g5LiN55+l5rGf5pyI5b6F5L2V5Lq6LCDkvYbop4Hplb/msZ/pgIHmtYHmsLQu").encode(
            "utf-8")
        genesis_user_pk = [
            'cf417a2d543461710fef6ab774a2c4b15c33758b1a26bbb9087e696f0b9f22d670a8d5fa732dd43c2023f4aef2f5930a1f73d7690c8b6c19b8ffb78b168999e1cf8679d72c1a43d15d2f5dba98cb9b9484fb9803f9e7c59e0ec8aa8bb3020c7c',
            'cf417a2d543461710fef6ab774a2c4b15c33758b1a26bbb9087e696f0b9f22d670a8d5fa732dd43c2023f4aef2f5930a1f73d7690c8b6c19b8ffb78b168999e1cf8679d72c1a43d15d2f5dba98cb9b9484fb9803f9e7c59e0ec8aa8bb3020c7c']
        genesis_body_signature = [
            '4571c8f7fe2ce679f6387ebce85a95a93b1185d8223e7df1eed006fd9a9d6c1f8650927cc76a24b4bd593bbec391ee55f6998694db9b3495d83f1396bd2d7f46828be894b420340adebc97d92245857919ecc826fa23f150d3ef0a268942a2ff',
            '4571c8f7fe2ce679f6387ebce85a95a93b1185d8223e7df1eed006fd9a9d6c1f8650927cc76a24b4bd593bbec391ee55f6998694db9b3495d83f1396bd2d7f46828be894b420340adebc97d92245857919ecc826fa23f150d3ef0a268942a2ff']
        header = {
            "blockID": "be0z87ef7017c199bebdfa50ba6d4321daa1",  # 区块ID
            "timestamp": 1648181482375,
            "epoch": 0,
            "prevBlock": genesis_pre_block_header,  # 上一个区块的哈希值列表
            "prevBlockHeader": genesis_pre_block,  # 上一个区块的头部哈希值列表
            "userPK": genesis_user_pk,  # 生成该区块的用户公钥
            "bodySignature": genesis_body_signature,  # 签名,第一个是简单节点用户的签名，第二个是主节点用户的签名，若只有一个，则为主节点用户的签名
            "bodyEncoding": "utf-8",  # 内容编码方式
            "blockType": "b"
        }
        self.__BlockOfBeings = NewBlockOfBeingsByExist(header=header, body=genesis_body).getBlock()

    def getBlockOfBeings(self):
        block = self.__BlockOfBeings
        for i in range(2):
            if not CipherSuites.verify(pk=block.getUserPk()[i], signature=block.getBodySignature()[i],
                                       message=block.body):
                raise "签名错误，公钥：" + str(block.getUserPk()[i])
        return block


if __name__ == "__main__":
    a = GenesisBlock().getBlockOfBeings()
