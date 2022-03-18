import base64

from core.data.block_of_beings import BlockOfBeings
from core.user.user import User
from core.utils.ciphersuites import CipherSuites


# 创世区块
class GenesisBlock:
    def __init__(self):
        genesis_pre_block_header = "0" * 64
        genesis_pre_block = "0" * 64
        genesis_body = base64.b64encode(str("江畔何人初见月? 江月何年初照人? 人生代代无穷已, 江月年年只相似. 不知江月待何人, 但见长江送流水.").encode("utf-8"))
        genesis_user_pk = [
            '81dfa9833d8487629176c354b4f537a953154a710a677c97a493aa52a4dc12201f39e68566acd8bdae7526a2d148fdd48fa5c56dc07552d50fc80d5efaefe56f155158219394907b2a621b5b442fe7e75656bb11c8092b709fde8b35c82d0f06',
            '81dfa9833d8487629176c354b4f537a953154a710a677c97a493aa52a4dc12201f39e68566acd8bdae7526a2d148fdd48fa5c56dc07552d50fc80d5efaefe56f155158219394907b2a621b5b442fe7e75656bb11c8092b709fde8b35c82d0f06']
        genesis_body_signature = [
            '3bd7bf50578aaf3b8c33864c813d00d06218fb483cce388b1fdb86db82c1314d9f25b3406c3d9dc4d1d6d650f92872d57c46388e5e08d1e143e2ad993ac448845ec7135c3e0fa36a095788d45ca4ed916baf1306c982180b0e16b5f84492f1f8',
            '3bd7bf50578aaf3b8c33864c813d00d06218fb483cce388b1fdb86db82c1314d9f25b3406c3d9dc4d1d6d650f92872d57c46388e5e08d1e143e2ad993ac448845ec7135c3e0fa36a095788d45ca4ed916baf1306c982180b0e16b5f84492f1f8']
        self.__BlockOfBeings = BlockOfBeings(epoch=0, prev_block_header=genesis_pre_block_header,
                                             pre_block=genesis_pre_block, user_pk=genesis_user_pk,
                                             body_signature=genesis_body_signature, body=genesis_body)

    def getBlockOfBeings(self):
        block = self.__BlockOfBeings
        for i in range(2):
            if not CipherSuites.verify(pk=block.getUserPk()[i], signature=block.getBodySignature()[i],
                                       message=block.body):
                raise "签名错误，公钥：" + str(block.getUserPk()[i])
        return block
