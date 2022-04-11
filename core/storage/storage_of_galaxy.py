from ast import literal_eval

from core.consensus.block_generate import NewBlockOfTimesByExist
from core.storage.sqlite import Sqlite
from core.data.block_of_times import BlockOfTimes, BodyOfTimesBlock
from core.utils.ciphersuites import CipherSuites


class StorageOfGalaxy(Sqlite):
    def __init__(self):
        super().__init__()

    def addBlockOfGalaxy(self, block_of_galaxy: BlockOfTimes):
        election_period = block_of_galaxy.electionPeriod
        block_id = block_of_galaxy.getBlockID()
        user_pk = str(block_of_galaxy.getUserPk()).encode("utf-8")
        header = str(block_of_galaxy.getBlockHeader()).encode("utf-8")
        body = block_of_galaxy.body
        cursor = self.blockConn.cursor()
        cursor.execute("""
        insert into galaxy(election_period, block_id, user_pk, header, body) values (?,?,?,?,?)
        """, (election_period, block_id, user_pk, header, body))
        self.blockConn.commit()

    def isExitBlockOfGalaxy(self, user_pk, beings_block_id, beings_simple_user_pk, beings_main_node_user_pk):
        body_of_times_block = BodyOfTimesBlock(users_pk=[beings_simple_user_pk, beings_main_node_user_pk],
                                               block_id=beings_block_id).getBody()
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select count(id) from galaxy
        where user_pk = ? and body = ?
        """, (user_pk, str(body_of_times_block).encode("utf-8")))
        res = cursor.fetchone()
        if res[0] > 0:
            return True
        else:
            return False

    def getBlockAbstractByElectionPeriod(self, election_period) -> []:
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select header,body
        from galaxy where election_period = ?
        """, (election_period,))
        res_list = cursor.fetchall()
        if res_list is None:
            # 上一选举阶段无选取区块生成
            return [None, None]
        block_header_join = ""
        block_join = ""
        for res in res_list:
            header = literal_eval(bytes(res[0]).decode())
            body = res[1]
            block_of_times = NewBlockOfTimesByExist(header=header, body=body).getBlock()
            block_header_join += block_of_times.getBlockHeaderSHA256()
            block_join += block_of_times.getBlockSHA256()

        block_header_abstract = CipherSuites.generateSHA256(block_header_join)
        block_abstract = CipherSuites.generateSHA256(block_join)
        return [block_header_abstract, block_abstract]
