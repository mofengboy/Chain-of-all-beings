from ast import literal_eval

from core.storage.sqlite import Sqlite
from core.data.block_of_galaxy import BlockOfGalaxy
from core.utils.ciphersuites import CipherSuites


class StorageOfGalaxy(Sqlite):
    def __init__(self):
        super().__init__()

    def addBlockOfGalaxy(self, block_of_galaxy: BlockOfGalaxy):
        election_period = block_of_galaxy.electionPeriod
        block_id = block_of_galaxy.getBlockID()
        user_pk = block_of_galaxy.getUserPk()
        header = str(block_of_galaxy.getBlockHeader()).encode("utf-8")
        body = block_of_galaxy.body
        cursor = self.blockConn.cursor()
        cursor.execute("""
        insert into galaxy(election_period, block_id, user_pk, header, body) values (?,?,?,?,?)
        """, (election_period, block_id, user_pk, header, body))
        self.blockConn.commit()

    def getBlockAbstractByElectionPeriod(self, election_period) -> []:
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select election_period,block_id,user_pk,header,body
         from galaxy where election_period= ?
        """, (election_period,))
        res_list = cursor.fetchall()
        if len(res_list) == 0:
            # 上一选举阶段无选取区块生成
            return [None, None]
        block_header_join = ""
        block_join = ""
        for res in res_list:
            election_period = res[1]
            user_pk = res[3]
            header = literal_eval(bytes(res[4]).decode())
            body = res[5]
            block_of_galaxy = BlockOfGalaxy(election_period=election_period,
                                            prev_block_header=header["prevBlockHeader"],
                                            pre_block=header["prevBlock"], user_pk=user_pk,
                                            body_signature=header["bodySignature"], body=body)
            block_of_galaxy.setHeader(header=header)
            block_header_join += block_of_galaxy.getBlockHeaderSHA256()
            block_join += block_of_galaxy.getBlockSHA256()

        block_header_abstract = CipherSuites.generateSHA256(block_header_join)
        block_abstract = CipherSuites.generateSHA256(block_join)
        return [block_header_abstract, block_abstract]
