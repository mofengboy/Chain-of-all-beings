import logging
import os
import sqlite3

# web server数据库
from ast import literal_eval

from core.consensus.data import VoteMessage, LongTermVoteMessage
from core.data.block_of_beings import BlockListOfBeings
from core.utils.serialization import SerializationAssetOfBeings, SerializationVoteMessage, \
    SerializationLongTermVoteMessage

logger = logging.getLogger("main")


class DB:
    def __init__(self):
        self.__DB = sqlite3.connect('../server/db/database.db', check_same_thread=False)
        self.__initDB()

    def __initDB(self):
        cursor = self.__DB.cursor()
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'beings_block'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table beings_block(
            id INTEGER PRIMARY KEY,
            user_pk TEXT NOT NULL,
            body BLOB NOT NULL,
            signature TEXT NOT NULL,
            is_review INTEGER NOT NULL,
            review_username TEXT,
            create_time TEXT NOT NULL
            )
            """)
            self.__DB.commit()

        # 用户为了成为主节点提交的申请书
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'application_form'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table application_form(
            id INTEGER PRIMARY KEY,
            node_id TEXT NOT NULL,
            user_pk TEXT NOT NULL,
            node_ip  TEXT NOT NULL,
            server_url TEXT NOT NULL,
            node_create_time TEXT NOT NULL,
            node_signature TEXT NOT NULL,
            application TEXT NOT NULL,
            application_signature TEXT NOT NULL,
            is_review INTEGER NOT NULL,
            remarks TEXT NOT NULL,
            create_time TEXT NOT NULL
            )
            """)
            self.__DB.commit()

        # 推荐中的众生区块信息
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'times_block_queue'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table times_block_queue(
            id INTEGER PRIMARY KEY,
            election_period INTEGER NOT NULL,
            beings_block_id TEXT NOT NULL,
            votes FLOAT NOT NULL,
            vote_list BLOB NOT NULL,
            status INTEGER NOT NULL,
            create_time TEXT NOT NULL
            )
            """)
            self.__DB.commit()

    def getWaitingBlockListOfBeingsToSDK(self):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id,user_pk,body,signature,is_review,create_time 
        from beings_block where is_review = 1 limit 10
        """)
        data_list = cursor.fetchall()
        block_list = []
        for data in data_list:
            block_list.append({
                "db_id": data[0],
                "user_pk": data[1],
                "body": data[2],
                "signature": data[3],
                "is_review": data[4],
                "create_time": data[5]
            })
            cursor.execute("""
            update beings_block set is_review = 3
            where id = ?
            """, (data[0],))

        self.__DB.commit()
        return block_list

    def getWaitingBlockCountOfBeingsToSDK(self):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select count(id)
        from beings_block where is_review = 1
        """)
        data = cursor.fetchone()
        return data[0]

    def getWaitingApplicationFormToSDK(self):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id, node_id, user_pk, node_ip, server_url, node_create_time, node_signature, 
        application, application_signature, is_review, create_time
        from application_form where is_review = 1 limit 2
        """)
        data_list = cursor.fetchall()
        application_form_list = []
        for data in data_list:
            application_form_list.append({
                "db_id": data[0],
                "node_id": data[1],
                "user_pk": data[2],
                "node_ip": data[3],
                "server_url": data[4],
                "node_create_time": data[5],
                "node_signature": data[6],
                "application": data[7],
                "application_signature": data[8],
                "is_review": data[9],
                "create_time": data[10]
            })
            cursor.execute("""
            update application_form set is_review = 3
            where id = ?
            """, (data[0],))
        self.__DB.commit()
        return application_form_list

    def getWaitingApplicationFormCountToSDK(self):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select count(id)
        from application_form where is_review = 1
        """)
        data = cursor.fetchone()
        return data[0]

    def getSimpleUserVoteByUserPk(self, user_pk):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id, election_period, user_pk, total_vote, used_vote, update_time, create_time from simple_user_vote
        where user_pk = ?
        """, (user_pk,))
        res = cursor.fetchone()
        if res is not None:
            data = {
                "id": res[0],
                "election_period": res[1],
                "user_pk": res[2],
                "total_vote": res[3],
                "used_vote": res[4],
                "update_time": res[5],
                "create_time": res[6],
            }
            return data
        else:
            return None

    def addUsedVoteOfSimpleUser(self, user_pk, used_vote):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select used_vote from simple_user_vote
        where user_pk = ?
        """, (user_pk,))
        res = cursor.fetchone()
        if res is not None:
            original_used_vote = round(res[0], 1)
            print(original_used_vote)
            cursor.execute("""
            update simple_user_vote 
            set used_vote = ?
            where user_pk = ?
            """, (round(used_vote, 1) + original_used_vote, user_pk))
            self.__DB.commit()
            return self.getSimpleUserVoteByUserPk(user_pk)
        else:
            return None

    def isExitTimesBlockQueueByBlockId(self, beings_block_id):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select count(id) 
        from times_block_queue
        where beings_block_id = ?
        """, (beings_block_id,))
        res = cursor.fetchone()
        if res[0] > 0:
            return True
        else:
            return False

    def modifyStatusOfTimesBlockQueue(self, beings_block_id, status):
        cursor = self.__DB.cursor()
        cursor.execute("""
        update times_block_queue
        set status = ?
        where beings_block_id = ?
        """, (status, beings_block_id))
        self.__DB.commit()

    def getTimesBlockQueueByVotes(self, votes):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id, election_period, beings_block_id, votes, vote_list, status, create_time 
        from times_block_queue
        where status = 0 and votes >= ? limit 1
        """, (votes,))
        res = cursor.fetchone()
        if res is None:
            return None
        else:
            data = {
                "id": res[0],
                "election_period": res[1],
                "beings_block_id": res[2],
                "votes": res[3],
                "vote_list": literal_eval(bytes(res[4]).decode("utf-8")),
                "status": res[5],
                "create_time": res[6]
            }
            return data

    def addVoteOfTimesBlockQueue(self, beings_block_id, vote_message: VoteMessage):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select votes, vote_list from times_block_queue
        where beings_block_id = ? and status = ?
        """, (beings_block_id, 0))
        res = cursor.fetchone()
        if res is not None:
            raw_votes = round(res[0], 1)
            vote_list = literal_eval(bytes(res[1]).decode("utf-8"))
            vote_list.append(SerializationVoteMessage.serialization(vote_message))
            cursor.execute("""
            update times_block_queue
            set votes = ?, vote_list = ?
            where beings_block_id = ?
            """, (raw_votes + round(vote_message.numberOfVote, 1), str(vote_list).encode("utf-8"), beings_block_id))
            self.__DB.commit()

    def addPermanentVoteOfTimesBlockQueue(self, beings_block_id, long_term_vote_message: LongTermVoteMessage):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select votes, vote_list from times_block_queue
        where beings_block_id = ? and status = ?
        """, (beings_block_id, 0))
        res = cursor.fetchone()
        if res is not None:
            raw_votes = round(res[0], 1)
            vote_list = literal_eval(bytes(res[1]).decode("utf-8"))
            vote_list.append(SerializationLongTermVoteMessage.serialization(long_term_vote_message))
            cursor.execute("""
            update times_block_queue
            set votes = ?, vote_list = ?
            where beings_block_id = ?
            """, (raw_votes + round(long_term_vote_message.numberOfVote, 1), str(vote_list).encode("utf-8"),
                  beings_block_id))
            self.__DB.commit()


# core部分读取server部分的数据库
class SDK:
    def __init__(self):
        self.db = DB()

    def getBeings(self):
        data_list = self.db.getWaitingBlockListOfBeingsToSDK()
        beings_list = []
        for data in data_list:
            beings_list.append({
                "user_pk": data["user_pk"],
                "body_signature": data["signature"],
                "body": data["body"]
            })
        return beings_list

    def getBeingsCount(self):
        return self.db.getWaitingBlockCountOfBeingsToSDK()

    def getApplicationForm(self):
        data_list = self.db.getWaitingApplicationFormToSDK()
        application_form_list = []
        for data in data_list:
            application_form_list.append({
                "node_id": data["node_id"],
                "user_pk": data["user_pk"],
                "node_ip": data["node_ip"],
                "server_url": data["server_url"],
                "node_create_time": int(data["node_create_time"]),
                "node_signature": data["node_signature"],
                "application": data["application"],
                "application_signature": data["application_signature"]
            })
        return application_form_list

    def getApplicationFormCount(self):
        return self.db.getWaitingApplicationFormCountToSDK()

    def addUsedVoteOfSimpleUser(self, user_pk, used_vote):
        self.db.addUsedVoteOfSimpleUser(user_pk, used_vote)

    def isExitTimesBlockQueueByBlockId(self, beings_block_id):
        return self.db.isExitTimesBlockQueueByBlockId(beings_block_id)

    def addVoteOfTimesBlockQueue(self, beings_block_id, vote_message: VoteMessage):
        self.db.addVoteOfTimesBlockQueue(beings_block_id, vote_message)

    def addPermanentVoteOfTimesBlockQueue(self, beings_block_id, long_term_vote_message: LongTermVoteMessage):
        self.db.addPermanentVoteOfTimesBlockQueue(beings_block_id, long_term_vote_message)

    def getTimesBlockQueueByVotes(self, votes):
        return self.db.getTimesBlockQueueByVotes(votes)

    def modifyStatusOfTimesBlockQueue(self, beings_block_id, status):
        self.db.modifyStatusOfTimesBlockQueue(beings_block_id, status)


# server部分的区块资源
# 提供下载
class ChainAsset:
    def __init__(self):
        self.file_path = "../server/static/"
        os.makedirs(self.file_path, mode=666, exist_ok=True)

    # 通过Epoch检测众生区块是否存在
    def beingsIsExitByEpoch(self, epoch) -> bool:
        file = self.file_path + "beings_" + str(epoch) + ".chain"
        return os.path.exists(file)

    # 保存区块
    def saveBlockOfBeings(self, block_list_of_beings: BlockListOfBeings) -> bool:
        if len(block_list_of_beings.list) == 0:
            return True
        epoch = block_list_of_beings.list[0].getEpoch()
        block_list_of_beings.sortByBlockId()
        file_name = "beings_" + str(epoch) + ".chain"
        if not self.beingsIsExitByEpoch(epoch):
            with open(self.file_path + file_name, "wb+") as fp:
                content = SerializationAssetOfBeings.serialization(block_list_of_beings)
                fp.write(content)
        else:
            return False

    # 批量期次保存区块
    def saveBatchBlockOfBeings(self, block_list_of_beings: BlockListOfBeings) -> bool:
        epoch_block_list_of_beings = {}
        for block in block_list_of_beings.list:
            epoch = block.getEpoch()
            if str(epoch) not in epoch_block_list_of_beings:
                epoch_block_list_of_beings[str(epoch)] = BlockListOfBeings()
                epoch_block_list_of_beings[str(epoch)].addBlock(block)
            else:
                epoch_block_list_of_beings[str(epoch)].addBlock(block)
        is_success = True
        for block_list in epoch_block_list_of_beings.values():
            is_success = self.saveBlockOfBeings(block_list) and is_success
        return is_success
