from ast import literal_eval

from core.consensus.block_generate import NewBlockOfTimesByExist
from core.consensus.constants import LongTermVoteValidityPeriod
from core.storage.sqlite import Sqlite
from core.data.block_of_times import BlockOfTimes, BodyOfTimesBlock
from core.utils.ciphersuites import CipherSuites
from core.utils.serialization import SerializationTimes


class StorageOfGalaxy(Sqlite):
    def __init__(self):
        super().__init__()

    def addBlockOfGalaxy(self, block_of_galaxy: BlockOfTimes):
        election_period = block_of_galaxy.electionPeriod
        block_id = block_of_galaxy.getBlockID()
        user_pk = block_of_galaxy.getUserPk()[0]
        header = str(block_of_galaxy.getBlockHeader()).encode("utf-8")
        body = block_of_galaxy.body
        body_of_times_dict = literal_eval(bytes(body).decode("utf-8"))
        users_pk = body_of_times_dict["users_pk"]
        beings_block_id = body_of_times_dict["block_id"]
        cursor = self.blockConn.cursor()
        cursor.execute("""
        insert or ignore into galaxy(election_period, block_id, user_pk, header, body,beings_block_id,beings_simple_user_pk,beings_main_node_user_pk) 
        values (?,?,?,?,?,?,?,?)
        """, (election_period, block_id, user_pk, header, body, beings_block_id, users_pk[0], users_pk[1]))
        self.blockConn.commit()

    def addBatchBlockOfGalaxy(self, block_list_of_galaxy: list[BlockOfTimes]):
        data_list = []
        for block_of_galaxy_i in block_list_of_galaxy:
            election_period = block_of_galaxy_i.electionPeriod
            block_id = block_of_galaxy_i.getBlockID()
            user_pk = block_of_galaxy_i.getUserPk()[0]
            header = str(block_of_galaxy_i.getBlockHeader()).encode("utf-8")
            body = block_of_galaxy_i.body
            body_of_times_dict = literal_eval(bytes(body).decode("utf-8"))
            users_pk = body_of_times_dict["users_pk"]
            beings_block_id = body_of_times_dict["block_id"]
            data_list.append(
                (election_period, block_id, user_pk, header, body, beings_block_id, users_pk[0], users_pk[1])
            )
        cursor = self.blockConn.cursor()
        cursor.executemany("""
        insert or ignore into galaxy(election_period, block_id, user_pk, header, body, beings_block_id, beings_simple_user_pk, beings_main_node_user_pk) 
        VALUES (?,?,?,?,?,?,?,?)
        """, data_list)
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
        from galaxy 
        where election_period = ?
        ORDER BY block_id ASC
        """, (election_period,))
        res_list = cursor.fetchall()
        if len(res_list) == 0:
            # 上一选举阶段无选取区块生成
            return None, None
        block_header_join = ""
        block_join = ""
        for res in res_list:
            header = literal_eval(bytes(res[0]).decode())
            body = res[1]
            block_of_times = NewBlockOfTimesByExist(header=header, body=body).getBlock()
            block_header_join += block_of_times.getBlockHeaderSHA256()
            block_join += block_of_times.getBlockSHA256()
        block_header_abstract = CipherSuites.generateSHA256(str(block_header_join).encode("utf-8")).hexdigest()
        block_abstract = CipherSuites.generateSHA256(str(block_join).encode("utf-8")).hexdigest()
        return block_header_abstract, block_abstract

    def getListOfGalaxyBlockByElectionPeriod(self, start, end) -> list[BlockOfTimes]:
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select header, body 
        from galaxy
        where election_period >= ? and election_period < ?
        ORDER BY election_period, block_id ASC
        """, (start, end))
        res = cursor.fetchall()
        times_block_list = []
        for block_i in res:
            header = literal_eval(bytes(block_i[0]).decode("utf-8"))
            times_block = NewBlockOfTimesByExist(header=header, body=block_i[1]).getBlock()
            times_block_list.append(times_block)
        return times_block_list

    def getMainNodeUserCount(self, main_node_user_pk, election_period):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select count(id)
        from galaxy
        where user_pk = ? or beings_main_node_user_pk = ? and election_period >= ?
        """, (main_node_user_pk, main_node_user_pk, election_period - 128))
        res = cursor.fetchone()
        if res is None:
            return 0
        else:
            return res[0]

    def getSimpleUserCount(self, simple_user_pk):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select count(id)
        from galaxy
        where beings_simple_user_pk = ?
        """, (simple_user_pk,))
        res = cursor.fetchone()
        if res is None:
            return 0
        else:
            return res[0]

    def getSimpleUserCountOfPermanentVote(self, current_election_period: int):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select count(id)
        from galaxy
        where election_period >= ?
        """, (current_election_period - LongTermVoteValidityPeriod))
        res = cursor.fetchone()
        return res[0]

    def computeSimpleUserInfoOfPermanentVote(self, current_election_period: int) -> dict:
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select beings_simple_user_pk
        from galaxy
        where election_period >= ?
        """, (current_election_period - LongTermVoteValidityPeriod,))
        res = cursor.fetchall()
        data_dict = {}
        for data_i in res:
            simple_user_pk_i = data_i[0]
            if simple_user_pk_i in data_dict.keys():
                data_dict[simple_user_pk_i] += 1
            else:
                data_dict[simple_user_pk_i] = 1
        return data_dict
