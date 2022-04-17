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
        try:
            cursor = self.blockConn.cursor()
            data_list = []
            for block in blockListOfBeings.list:
                data_list.append(
                    (block.getEpoch(), block.getBlockID(), block.getUserPk()[0], block.getUserPk()[1],
                     str(block.getBlockHeader()).encode("utf-8"),
                     block.body)
                )
            cursor.executemany("""
                insert into beings (epoch,block_id,simple_user_pk,main_node_user_pk,header,body)
                values (?,?,?,?,?,?);
                """, data_list)
            self.blockConn.commit()
            logger.info("已保存当前众生区块列表，数量为：" + str(len(data_list)))
        except Exception as err:
            logger.warning(err)

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
        select header,body,simple_user_pk,main_node_user_pk
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
            block_of_beings = BlockOfBeings(epoch=max_epoch, prev_block_header=prevBlockHeader,
                                            user_pk=block_header["userPK"],
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
        select header,body
        from beings order by epoch,block_id desc limit 0,1;
        """)
        res = cursor.fetchone()
        if res is None:
            return None
        else:
            block_header = literal_eval(bytes(res[0]).decode("utf-8"))
            prevBlock = block_header["prevBlock"]
            prevBlockHeader = block_header["prevBlockHeader"]
            bodySignature = block_header["bodySignature"]
            body = res[1]
            block_of_beings = BlockOfBeings(epoch=block_header["epoch"], prev_block_header=prevBlockHeader,
                                            user_pk=block_header["userPK"],
                                            pre_block=prevBlock, body_signature=bodySignature, body=body)
            block_of_beings.setHeader(header=block_header)
            return block_of_beings

    # 包括start不包括end
    def getBlocksByEpoch(self, start, end) -> []:
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select header, body 
        from beings where epoch >= ? and epoch < ?
        """, (start, end))
        res = cursor.fetchall()
        block_list = []
        for block_dict in res:
            block = NewBlockOfBeingsByExist(header=literal_eval(bytes(block_dict[0]).decode("utf-8")),
                                            body=block_dict[1]).getBlock()
            block_list.append(SerializationBeings.serialization(block_of_beings=block))
        return block_list

    def delBlocksByEpoch(self, start, end):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        delete from beings where epoch >= ? and epoch < ?
        """, (start, end))
        self.blockConn.commit()

    def saveBatchBlock(self, block_list: BlockListOfBeings):
        try:
            data_list = []
            for block in block_list.list:
                data_list.append(
                    [block.getEpoch(), block.getBlockID(), block.getUserPk()[0], block.getUserPk()[1],
                     str(block.getBlockHeader()).encode("utf-8"), block.body])
            cursor = self.blockConn.cursor()
            cursor.executemany("""
            insert into beings(epoch,block_id,simple_user_pk,main_node_user_pk,header,body) 
            values(?,?,?,?,?,?) 
            """, data_list)
            self.blockConn.commit()
        except Exception as err:
            logger.warning(err)

    # 获取当前用户在此范围内的数量
    def getUserCountByEpoch(self, user_pk, start, end):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select count(id) from beings 
        where main_node_user_pk = ?
        and epoch >= ? and epoch < ?
        """, (user_pk, start, end))
        res = cursor.fetchone()
        logger.debug("获取当前用户在此范围内的数量")
        logger.debug(res)
        if res is None:
            return 0
        else:
            return res[0]

    def getUserPkByBlockId(self, block_id) -> []:
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select simple_user_pk,main_node_user_pk from beings 
        where block_id = ?
        """, (block_id,))
        res = cursor.fetchone()
        return [res[0], res[1]]

    def getMaxEpoch(self):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select max(epoch) from beings
        """)
        res = cursor.fetchone()
        if res[0] is None:
            return 0
        return res[0]
