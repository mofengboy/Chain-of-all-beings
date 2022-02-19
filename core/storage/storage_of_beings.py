from ast import literal_eval

from core.storage.sqlite import Sqlite
from core.data.block_of_beings import BlockOfBeings, BlockListOfBeings


class StorageOfBeings(Sqlite):
    def __init__(self):
        super().__init__()
        self.currentBlockListOfBeing = BlockListOfBeings()

    def saveCurrentBlockOfBeings(self, blockListOfBeings: BlockListOfBeings):
        self.currentBlockListOfBeing = blockListOfBeings.copy()

        cursor = self.blockConn.cursor()
        data_list = []
        for block in blockListOfBeings.getList():
            data_list.append(
                (block.getEpoch(), block.getBlockID(), str(block.getUserPk()),
                 str(block.getBlockHeader()).encode("utf-8"),
                 block.body)
            )

        cursor.executemany("""
            insert into beings (epoch,block_id,user_pk,header,body)
            values (?,?,?,?,?);
            """, data_list)
        self.blockConn.commit()

    def getLastBlockByCache(self) -> BlockOfBeings:
        return self.currentBlockListOfBeing.getBlockByMaxBlockId()

    def getLastBlock(self) -> BlockOfBeings:
        cursor = self.blockConn.cursor()
        # 其中order by id desc 是按照id降序排列；limit 0,1中0是指从偏移量为0（也就是从第1条记录）开始，1是指需要查询的记录数，这里只查询1条记录
        cursor.execute("""
        select epoch,block_id,user_pk,header,body
         from beings order by id desc limit 0,1;
        """)
        res = cursor.fetchone()
        block_header = literal_eval(bytes.decode(res[3]))
        prevBlock = block_header["prevBlock"]
        prevBlockHeader = block_header["prevBlockHeader"]
        bodySignature = block_header["bodySignature"]
        body = res[4]

        block_of_beings = BlockOfBeings(epoch=res[0], prev_block_header=prevBlockHeader, user_pk=res[2],
                                        pre_block=prevBlock, body_signature=bodySignature, body=body)
        block_of_beings.setHeader(header=block_header)
        return block_of_beings

    # 包括start不包括end
    def getBlocksByEpoch(self, start, end) -> []:
        cursor = self.blockConn.cursor()
        res = cursor.execute("""
        select user_pk from beings where epoch >= ? and epoch < ?
        """, (start, end))
        main_node_user_pk_list = []
        for user_pk_i in res:
            main_node_user_pk_list.append(user_pk_i[1])
        return main_node_user_pk_list

    # 获取当前用户在此范围内的数量
    def getUserCountByEpoch(self, user_pk, start, end):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select count(user_pk) from beings where user_pk = ? and epoch >= ? and epoch < ?
        """, (user_pk, start, end))
        res = cursor.fetchone()
        if res is None:
            return 0
        else:
            return res[0]

    def getUserPkByBlockId(self, block_id) -> []:
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select user_pk from beings where block_id = ?
        """, (block_id,))
        res = cursor.fetchone()
        res = literal_eval(res[0])
        return res


if __name__ == "__main__":
    storageOfBeings = StorageOfBeings()
    storageOfBeings.getUserPkByBlockId(block_id="aaa")

    # user = User()
    # user.register()
    # genesis_user_sk = user.getUserSK()
    # genesis_user_pk = user.getUserPKString()
    #
    # genesis_block_id = 0
    # genesis_pre_block_header = "0" * 256
    # genesis_pre_block = "0" * 256
    #
    # genesis_body = "江畔何人初见月? 江月何年初照人? 人生代代无穷已, 江月年年只相似. 不知江月待何人, 但见长江送流水."
    # genesis_body_signature = [user.sign(genesis_body)]
    #
    # GenesisBlock = BlockOfBeings(epoch=0,
    #                              prev_block_header=genesis_pre_block_header,
    #                              pre_block=genesis_pre_block, user_pk=genesis_user_pk,
    #                              body_signature=genesis_body_signature, body=genesis_body)
    #
    # block_list_of_beings = BlockListOfBeings()
    # block_list_of_beings.addBlock(GenesisBlock)
    # storageOfBeings.getLastBlock()
