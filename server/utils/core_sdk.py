import sqlite3
import time
from ast import literal_eval
from core.config.cycle_Info import ElectionPeriodValue
from core.data.node_info import NodeInfo
from core.data.vote_info import WaitVote


class DBOfTemp:
    def __init__(self):
        self.tempConn = sqlite3.connect('../core/db/temp.db', check_same_thread=False)

    def getNodeInfo(self) -> NodeInfo:
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select content from core_info
        where info_name = ?
        """, ("node_info",))
        res = cursor.fetchone()
        node_info_dict = literal_eval(bytes(res[0]).decode("utf-8"))
        node_info = NodeInfo(node_id=node_info_dict["node_id"], user_pk=node_info_dict["user_pk"],
                             node_ip=node_info_dict["node_ip"], server_url=node_info_dict["server_url"],
                             create_time=node_info_dict["create_time"])
        node_info.setNodeSignature(node_info_dict["signature"])
        return node_info

    # 查询接受到的待审核的新节点数量
    def getCountOfNodeApply(self):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select count(*) from node_join_other where is_audit = 0
        """)
        res = cursor.fetchone()
        data_count = res[0]
        return data_count

    # 获取从其他主节点接受到的等待审核的申请表列表id
    def getListOfWaitingApplicationForm(self, offset, count):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select id, create_time from node_join_other
        where is_audit = 0 and id >= ? limit ?
        """, (offset, count))
        res = cursor.fetchall()
        id_list = []
        for data in res:
            id_list.append({
                "id": data[0],
                "create_time": data[1]
            })
        return id_list

    # 获取从其他主节点接受到的等待审核的申请表
    def getWaitingApplicationForm(self, db_id):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select id, node_id, user_pk, node_ip, server_url, node_create_time, 
        node_signature, application, application_signature, 
        main_node_user_pk, main_node_signature, is_audit, create_time 
        from node_join_other
        where id = ?
        """, (db_id,))
        application_form = cursor.fetchone()
        return application_form

    # 审核从其他主节点接受到的等待审核的申请表
    def auditWaitingApplicationForm(self, db_id, is_audit):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        update node_join_other set is_audit = ?
        where id = ?
        """, (is_audit, db_id))
        self.tempConn.commit()

    def getEpoch(self):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select content from core_info
        where info_name = ?
        """, ("current_epoch",))
        res = cursor.fetchone()
        if res is None:
            return 0
        else:
            return int(res[0])

    @staticmethod
    def getElectionPeriodValue():
        return ElectionPeriodValue

    def addVoteMessage(self, election_period, to_node_id, block_id, vote, simple_user_pk, signature):
        wait_vote = WaitVote()
        wait_vote.setInfo(election_period=election_period, to_node_id=to_node_id, block_id=block_id,
                          vote=vote, simple_user_pk=simple_user_pk)
        wait_vote.setSignature(signature)
        cursor = self.tempConn.cursor()
        cursor.execute("""
        insert into wait_votes(to_node_id, election_period, block_id, user_pk, vote_info, signature, status, create_time)
        values (?,?,?,?,?,?,?,?)
        """, (to_node_id, election_period, block_id, simple_user_pk, str(wait_vote.getInfo()).encode("utf-8"),
              signature, 0, time.time()))
        self.tempConn.commit()

    # def get


class DBOfBlock:
    def __init__(self):
        self.blockConn = sqlite3.connect('../core/db/block.db', check_same_thread=False)

    def getMaxEpoch(self):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select max(epoch) from beings
        """)
        res = cursor.fetchone()
        return res[0]

    def getEpochList(self, offset, count):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select epoch from beings
        where epoch >= ? and epoch < ?
        """, (offset, offset + count))
        res = cursor.fetchall()
        epoch_list = []
        for data in res:
            epoch_list.append(data[0])
        return epoch_list

    # 获取众生区块id列表
    def getIDListOfBeingsByEpoch(self, start, end):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select id,block_id,epoch,body from beings 
        where epoch >= ? and epoch < ?
        """, (start, end))
        res = cursor.fetchall()
        id_list = []
        for data in res:
            id_list.append({
                "id": data[0],
                "block_id": data[1],
                "epoch": data[2],
                "body_digest": bytes(data[3]).decode("utf-8")[0:172]
            })
        return id_list

    # 获取众生区块id列表
    def getIDListOfBeingsByOffset(self, offset, count):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select id,block_id,epoch,body from beings 
        order by id desc limit ?,?
        """, (offset, count))
        res = cursor.fetchall()
        id_list = []
        for data in res:
            id_list.append({
                "id": data[0],
                "block_id": data[1],
                "epoch": data[2],
                "body_digest": bytes(data[3]).decode("utf-8")[0:172]
            })
        return id_list

    def getBlockOfBeingsByBlockId(self, block_id):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select id,header,body from beings
        where block_id = ?
        """, (block_id,))
        res = cursor.fetchone()
        header = literal_eval(bytes(res[1]).decode("utf-8"))
        beings_dict = {
            "id": res[0],
            "block_id": header["blockID"],
            "epoch": header["epoch"],
            "prev_block": header["prevBlock"],
            "prev_block_header": header["prevBlockHeader"],
            "user_pk": header["userPK"],
            "body_signature": header["bodySignature"],
            "body": bytes(res[2]).decode("utf-8"),
            "timestamp": header["timestamp"]
        }
        return beings_dict

    def getListOfSimpleUser(self, main_node_user_pk, start_epoch, end_epoch):
        cursor = self.blockConn.cursor()
        cursor.execute("""
        select user_pk from beings
        where user_pk like ? and epoch >= ? and epoch < ?
        """, ("%" + main_node_user_pk + "%", start_epoch, end_epoch))
        res = cursor.fetchall()
        list_of_simple_user = {}
        for data_i in res:
            data = literal_eval(bytes(data_i[0]).decode("utf-8"))
            if data[0] in list_of_simple_user.keys():
                list_of_simple_user[data[0]] += 1
            else:
                list_of_simple_user[data[0]] = 1
        return list_of_simple_user


class VoteOfMainNode:
    def __init__(self):
        self.tempConn = sqlite3.connect('../core/db/temp.db', check_same_thread=False)

    @staticmethod
    def getElectionPeriodValue():
        return ElectionPeriodValue

    def getListOfMainNodeVote(self):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select main_node_id, main_node_user_pk from main_node_vote
        """)
        res = cursor.fetchall()
        data_list = []
        for data in res:
            data_list.append({
                "node_id": data[0],
                "node_user_pk": data[1]
            })
        return data_list

    def getMainNodeVoteByMainNodeUserPk(self, main_node_user_pk):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select id, main_node_id, main_node_user_pk, total_vote, used_vote, update_time, create_time
        from main_node_vote
        where main_node_user_pk = ?
        """, (main_node_user_pk,))
        res = cursor.fetchone()
        if res is not None:
            return {
                "id": res[0],
                "main_node_id": res[1],
                "main_node_user_pk": res[2],
                "total_vote": res[3],
                "used_vote": res[4],
                "update_time": res[5],
                "create_time": res[6],
            }
        else:
            return None
