from ast import literal_eval

from core.consensus.block_generate import NewBlockOfGarbageByExist
from core.data.block_of_garbage import BlockOfGarbage, BodyOfGarbageBlock
from core.storage.sqlite import Sqlite
from core.utils.ciphersuites import CipherSuites


class StorageOfGarbage(Sqlite):
    def __init__(self):
        super().__init__()

    def addBlockOfGarbage(self, block_of_garbage: BlockOfGarbage):
        election_period = block_of_garbage.electionPeriod
        block_id = block_of_garbage.getBlockID()
        user_pk = block_of_garbage.getUserPk()[0]
        header = str(block_of_garbage.getBlockHeader()).encode("utf-8")
        body = block_of_garbage.body
        body_of_garbage_dict = literal_eval(bytes(body).decode("utf-8"))
        users_pk = body_of_garbage_dict["users_pk"]
        beings_block_id = body_of_garbage_dict["block_id"]
        cursor = self.blockConn.cursor()
        cursor.execute("""
        insert into garbage(election_period, block_id, user_pk, header, body,beings_block_id,beings_simple_user_pk,beings_main_node_user_pk) 
        values (?,?,?,?,?,?,?,?)
        """, (election_period, block_id, user_pk, header, body, beings_block_id, users_pk[0], users_pk[1]))
        self.blockConn.commit()

    def addBatchBlockOfGarbage(self, block_list_of_garbage: list[BlockOfGarbage]):
        data_list = []
        for block_of_garbage_i in block_list_of_garbage:
            election_period = block_of_garbage_i.electionPeriod
            block_id = block_of_garbage_i.getBlockID()
            user_pk = block_of_garbage_i.getUserPk()[0]
            header = str(block_of_garbage_i.getBlockHeader()).encode("utf-8")
            body = block_of_garbage_i.body
            body_of_times_dict = literal_eval(bytes(body).decode("utf-8"))
            users_pk = body_of_times_dict["users_pk"]
            beings_block_id = body_of_times_dict["block_id"]
            data_list.append(
                (election_period, block_id, user_pk, header, body, beings_block_id, users_pk[0], users_pk[1])
            )
        cursor = self.blockConn.cursor()
        cursor.execute("""
        insert or ignore into garbage(election_period, block_id, user_pk, header, body, beings_block_id, beings_simple_user_pk, beings_main_node_user_pk) 
        VALUES (?,?,?,?,?,?,?,?)
        """, data_list)
        self.blockConn.commit()

    def isExitBlockOfGarbage(self, user_pk, beings_block_id, beings_simple_user_pk, beings_main_node_user_pk):
        body_of_garbage_block = BodyOfGarbageBlock(users_pk=[beings_simple_user_pk, beings_main_node_user_pk],
                                                   block_id=beings_block_id).getBody()
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select count(id) from garbage
        where user_pk = ? and body = ?
        """, (user_pk, str(body_of_garbage_block).encode("utf-8")))
        res = cursor.fetchone()
        if res[0] > 0:
            return True
        else:
            return False

    def getBlockAbstractByElectionPeriod(self, election_period) -> []:
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select header,body
        from garbage 
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
            block_of_garbage = NewBlockOfGarbageByExist(header=header, body=body).getBlock()
            block_header_join += block_of_garbage.getBlockHeaderSHA256()
            block_join += block_of_garbage.getBlockSHA256()
        block_header_abstract = CipherSuites.generateSHA256(str(block_header_join).encode("utf-8")).hexdigest()
        block_abstract = CipherSuites.generateSHA256(str(block_join).encode("utf-8")).hexdigest()
        return block_header_abstract, block_abstract

    def getListOfGarbageBlockByElectionPeriod(self, start, end) -> list[BlockOfGarbage]:
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select header, body 
        from garbage
        where election_period >= ? and election_period < ?
        """, (start, end))
        res = cursor.fetchall()
        garbage_block_list = []
        for block_i in res:
            header = literal_eval(bytes(block_i[0]).decode("utf-8"))
            garbage_block = NewBlockOfGarbageByExist(header=header, body=block_i[1]).getBlock()
            garbage_block_list.append(garbage_block)
        return garbage_block_list

    def getMainNodeUserCount(self, main_node_user_pk, election_period):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select count(id)
        from garbage
        where user_pk = ? and election_period >= ?
        """, (main_node_user_pk, election_period - 128))
        res = cursor.fetchone()
        if res is None:
            return 0
        else:
            return res[0]

    def getMainNodeOfBeingsBlockUserCount(self, main_node_user_pk):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select count(id)
        from garbage
        where beings_main_node_user_pk = ? 
        """, (main_node_user_pk,))
        res = cursor.fetchone()
        if res is None:
            return 0
        else:
            return res[0]

    def getSimpleUserCount(self, simple_user_pk):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select count(id)
        from garbage
        where beings_simple_user_pk = ?
        """, (simple_user_pk,))
        res = cursor.fetchone()
        if res is None:
            return 0
        else:
            return res[0]

    def getListOfSimpleUser(self) -> list:
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select beings_simple_user_pk
        from garbage
        """)
        simple_user_list = []
        res = cursor.fetchall()
        for data_i in res:
            simple_user_list.append(data_i[0])
        return simple_user_list
