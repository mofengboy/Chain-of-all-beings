from core.data.block_of_beings import BlockOfBeings
from core.utils.mongodb import DB


class GenesisBlock:
    def __init__(self):
        epoch = 0
        genesis_pre_block_header = "0" * 64
        genesis_pre_block = "0" * 64
        genesis_body = "江畔何人初见月? 江月何年初照人? 人生代代无穷已, 江月年年只相似. 不知江月待何人, 但见长江送流水." * 1024
        genesis_user_pk = '50e6dea791686095ffe7f58226ef59854b1d13819d865030eec085d05f1caebc63c15c5f0c1ccca66af087da7c369225b05eb8e1032a98c974efde1af284937225fe6f7de7e6a8503d23d4e7ec9d7810b3e788faed7b2cebc341c61a30ae0b91'
        genesis_body_signature = [
            '2bfbc9aefe38e35ec5d241a81b612c49cb82f1fd44c09616f5261caff11966dabce4281aabd847b27a9e6dab6082e3ba88575f56cac970279b4ab2b34699791b125d6f82e7e3b949c7ff789ffd5fa837065f69377c273b031cba40560861866e']
        self.__Block = BlockOfBeings(epoch=0, prev_block_header=genesis_pre_block_header,
                                     pre_block=genesis_pre_block, user_pk=genesis_user_pk,
                                     body_signature=genesis_body_signature, body=genesis_body)

    def getBlock(self):
        return self.__Block


if __name__ == "__main__":
    genesisBlock = GenesisBlock().getBlock()
    a = genesisBlock.getBlockHeaderSHA256()
    b = genesisBlock.getBlockSHA256()
    db = DB()
    db.insertBlockOfBeings(genesisBlock.getBlockHeader(), genesisBlock.body)

    print("")
