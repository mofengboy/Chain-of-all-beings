class BlockData:
    def __init__(self, header, body):
        self.header = header
        self.body = body


class BlockEpochData:
    def __init__(self, file):
        self.block_data_list = []
        with open(file, "rb") as f:
            for block_data in f:
                self.block_data_list