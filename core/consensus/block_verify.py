from core.storage.storage_of_beings import StorageOfBeings
from core.data.genesis_block import GenesisBlock
from core.utils.serialization import SerializationBeings


# 验证区块
class BlockVerify:
    def __init__(self, storage_of_beings: StorageOfBeings):
        self.storageOfBeings = storage_of_beings
        self.genesisBlock = GenesisBlock().getBlockOfBeings()

    # 验证0-epoch的区块
    def verifyBlockOfBeings(self, epoch):
        if epoch == 0:
            return 0
        start = 1
        last_block_header_list = [self.genesisBlock.getBlockHeaderSHA256()]
        last_block_list = [self.genesisBlock.getBlockSHA256()]
        while True:
            block_list = self.storageOfBeings.getBlocksByEpoch(start=start, end=start + 1)
            if len(block_list) == 0:
                start += 1
                continue
            if start >= epoch:
                return epoch
            temp_block_list = []
            for serial_block in block_list:
                block = SerializationBeings.deserialization(str(serial_block).encode("utf-8"))
                if block.getPrevBlockHeader() != last_block_header_list:
                    return block.getEpoch()
                if block.getPrevBlock() != last_block_list:
                    return block.getEpoch()
                temp_block_list.append(block)

            last_block_header_list = []
            last_block_list = []
            temp_block_list.sort(key=lambda x: x.getBlockID())
            for block in temp_block_list:
                last_block_header_list.append(block.getBlockHeaderSHA256())
                last_block_list.append(block.getBlockHeader())
            start += 1
