import logging
from ast import literal_eval

from core.consensus.block_generate import NewBlockOfBeingsByExist
from core.storage.sqlite import Sqlite
from core.data.block_of_beings import BlockOfBeings, BlockListOfBeings
from core.utils.serialization import SerializationBeings

logger = logging.getLogger("main")


class StorageOfBeings(Sqlite):
    def __init__(self):
        super().__init__()
        self.currentBlockListOfBeing = BlockListOfBeings()

    def saveCurrentBlockOfBeings(self, blockListOfBeings: BlockListOfBeings):
        self.currentBlockListOfBeing.list = blockListOfBeings.list.copy()
        self.currentBlockListOfBeing.listOfNoBlock = blockListOfBeings.listOfNoBlock.copy()

        cursor = self.blockConn.cursor()
        data_list = []
        for block in blockListOfBeings.list:
            data_list.append(
                (block.getEpoch(), block.getBlockID(), str(block.getUserPk()).encode("utf-8"),
                 str(block.getBlockHeader()).encode("utf-8"),
                 block.body)
            )

        cursor.executemany("""
            insert into beings (epoch,block_id,user_pk,header,body)
            values (?,?,?,?,?);
            """, data_list)
        self.blockConn.commit()
        logger.info("已保存当前众生区块列表，数量为：" + str(len(data_list)))

    def getBlockListByLastEpoch(self) -> BlockListOfBeings:
        if len(self.currentBlockListOfBeing.list) > 0:
            return self.currentBlockListOfBeing
        else:
            # 上一轮没有产生众生区块
            # 向前寻找
            return self.getLastBlockList()

    def getLastBlockList(self) -> BlockListOfBeings:
        cursor = self.blockConn.cursor()
        # 其中order by id desc 是按照id降序排列；limit 0,1中0是指从偏移量为0（也就是从第1条记录）开始，1是指需要查询的记录数，这里只查询1条记录
        cursor.execute("""
        select max(epoch)
        from beings 
        """)
        res1 = cursor.fetchone()
        max_epoch = res1[0]
        cursor.execute("""
        select header,body,user_pk
        from beings where epoch = ?
        """, (max_epoch,))
        res2 = cursor.fetchall()
        block_list_of_beings = BlockListOfBeings()
        for block_dict in res2:
            block_header = literal_eval(bytes.decode(block_dict[0]))
            prevBlock = block_header["prevBlock"]
            prevBlockHeader = block_header["prevBlockHeader"]
            bodySignature = block_header["bodySignature"]
            body = block_dict[1]
            block_of_beings = BlockOfBeings(epoch=max_epoch, prev_block_header=prevBlockHeader, user_pk=block_dict[2],
                                            pre_block=prevBlock, body_signature=bodySignature, body=body)
            block_of_beings.setHeader(header=block_header)
            block_list_of_beings.addBlock(block_of_beings)
        return block_list_of_beings

    def getLastBlockByCache(self) -> BlockOfBeings:
        if len(self.currentBlockListOfBeing.list) > 0:
            return self.currentBlockListOfBeing.getBlockByMaxBlockId()
        else:
            # 上一轮没有产生众生区块
            # 向前寻找
            return self.getLastBlock()

    def getLastBlock(self) -> BlockOfBeings:
        cursor = self.blockConn.cursor()
        # 其中order by id desc 是按照id降序排列；limit 0,1中0是指从偏移量为0（也就是从第1条记录）开始，1是指需要查询的记录数，这里只查询1条记录
        cursor.execute("""
        select epoch,block_id,user_pk,header,body
         from beings order by epoch,block_id desc limit 0,1;
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
        cursor.execute("""
        select id, epoch, block_id, user_pk, header, body 
        from beings where epoch >= ? and epoch < ?
        """, (start, end))
        res = cursor.fetchall()
        block_list = []
        for block_dict in res:
            block = NewBlockOfBeingsByExist(header=literal_eval(bytes(block_dict[4]).decode("utf-8")),
                                            body=block_dict[5]).getBlock()
            block_list.append(SerializationBeings.serialization(block_of_beings=block))
        return block_list

    def delBlocksByEpoch(self, start, end):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        delete from beings where epoch >= ? and epoch < ?
        """, (start, end))
        self.blockConn.commit()

    def saveBatchBlock(self, block_list: [BlockOfBeings]):
        data_list = []
        for block in block_list:
            data_list.append(
                [block.getEpoch(), block.getBlockID(), str(block.getUserPk()).encode("utf-8"),
                 str(block.getBlockHeader()).encode("utf-8"), block.body])
        cursor = self.blockConn.cursor()
        cursor.executemany("""
        insert into beings(epoch,block_id,user_pk,header,body) 
        values(?,?,?,?,?) 
        """, data_list)
        self.blockConn.commit()

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

    def getMaxEpoch(self):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select max(epoch) from beings
        """)
        res = cursor.fetchone()
        return res[0]


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
