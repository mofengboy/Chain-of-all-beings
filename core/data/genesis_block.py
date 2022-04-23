from core.consensus.block_generate import NewBlockOfBeingsByExist, NewBlockOfTimes, NewBlockOfGarbage
from core.data.block_of_beings import BlockOfBeings
from core.data.block_of_garbage import BodyOfGarbageBlock
from core.data.block_of_times import BodyOfTimesBlock
from core.user.user import User
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

    # 众生创世区块
    def getBlockOfBeings(self):
        block = self.__BlockOfBeings
        for i in range(2):
            if not CipherSuites.verify(pk=block.getUserPk()[i], signature=block.getBodySignature()[i],
                                       message=block.body):
                raise "签名错误，公钥：" + str(block.getUserPk()[i])
        return block

    # 时代创世区块
    # 注意每次生成的是不一样的
    def getBlockOfTimes(self):
        beings_block = self.getBlockOfBeings()
        beings_users_pk = [beings_block.getUserPk()[0], beings_block.getUserPk()[1]]
        body_of_times_block = BodyOfTimesBlock(users_pk=beings_users_pk, block_id=beings_block.getBlockID())
        body_signature = [
            "ec2d2cf7b4852abd7fd15ed28c9ce96b8c1a88556640836df0afa2db075b67f6a6f7678de2235b5e11fee9661777ace4b1141b47ae4d57fa3d009778d666cbcd7a1f134d9f09408288eabb191e72f41ae3ac5df7d2f4d865f56482007d8eb024"]
        user_pk = [
            "700ef6331d57fa7c4364c4bbac7cf7a19a50a7748403f88bca8e01a46c4dd1822ebe9b082ad11deeea9295add5fd0e4e2a66eacc024e13256f266857ad0dd51f714f380009044a4ce5eb22cedb60ac545b02e6fc748cec3dad2fb6ec550805b8"]
        block_of_times = NewBlockOfTimes(user_pk=user_pk, election_period=0,
                                         body_signature=body_signature, body=body_of_times_block, pre_block="0" * 64,
                                         prev_block_header="0" * 64).getBlock()
        if not CipherSuites.verify(pk=block_of_times.getUserPk()[0], signature=block_of_times.getBodySignature()[0],
                                   message=block_of_times.body):
            raise "签名错误，公钥：" + str(block_of_times.getUserPk()[0])
        return block_of_times

    # 垃圾创世区块
    # 注意每次生成的是不一样的
    def getBlockOfGarbage(self):
        beings_users_pk = ["0" * 192, "0" * 192]
        body_of_garbage_block = BodyOfGarbageBlock(users_pk=beings_users_pk, block_id="0" * 36)
        body_signature = [
            "648be53649c36a8f331103dfdf9d932b9e3f27002001b13688086d4167cb7472459b48ea3b1aea1751e28255945312c05d55ba1d5af1d2c529bacc4544eb8d9c072c594b51e99fab8131bd729c611c42d1e7782e312e9a19c9f8af257387a487"]
        user_pk = [
            "700ef6331d57fa7c4364c4bbac7cf7a19a50a7748403f88bca8e01a46c4dd1822ebe9b082ad11deeea9295add5fd0e4e2a66eacc024e13256f266857ad0dd51f714f380009044a4ce5eb22cedb60ac545b02e6fc748cec3dad2fb6ec550805b8"]
        block_of_garbage = NewBlockOfGarbage(user_pk=user_pk, election_period=0,
                                             body_signature=body_signature, body=body_of_garbage_block,
                                             pre_block="0" * 64,
                                             prev_block_header="0" * 64).getBlock()
        if not CipherSuites.verify(pk=block_of_garbage.getUserPk()[0], signature=block_of_garbage.getBodySignature()[0],
                                   message=block_of_garbage.body):
            raise "签名错误，公钥：" + str(block_of_garbage.getUserPk()[0])
        return block_of_garbage


if __name__ == "__main__":
    a = GenesisBlock().getBlockOfBeings()
    b = GenesisBlock().getBlockOfTimes()
    c = GenesisBlock().getBlockOfGarbage()
    print(c)
