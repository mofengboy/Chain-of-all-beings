from ast import literal_eval

from core.data.block_of_beings import BlockOfBeings
from core.consensus.block_generate import NewBlockOfBeingsByExist
from core.db.genesis_block import GenesisBlock


# 众生区块对象序列化与反序列化
class SerializationBeings:
    # 序列化
    @staticmethod
    def serialization(block_of_beings: BlockOfBeings):
        block_header = block_of_beings.getBlockHeader()
        body = block_of_beings.body
        data = {
            "header": block_header,
            "body": body
        }
        return data

    # 反序列化
    @staticmethod
    def deserialization(data_of_beings) -> BlockOfBeings:
        dict_of_beings = literal_eval(bytes(data_of_beings).decode("utf-8"))
        header = dict_of_beings["header"]
        body = dict_of_beings["body"]
        block_of_beings = NewBlockOfBeingsByExist(header=header, body=body).getBlock()
        return block_of_beings


if __name__ == "__main__":
    genesisBlock = GenesisBlock().getBlockOfBeings()
    data_of = Beings.serialization(genesisBlock)
    dict_of = Beings.deserialization(data_of)
    print(dict_of)
