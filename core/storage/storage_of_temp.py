from core.storage.sqlite import Sqlite
from core.utils.system_time import STime
from core.consensus.data import VoteInformation, ApplicationForm
from core.data.node_info import NodeInfo


class StorageOfTemp(Sqlite):
    def __init__(self):
        super().__init__()

    def saveData(self, user_pk, body_signature, body):
        create_time = STime.getTimestamp()
        cursor = self.tempConn.cursor()
        cursor.execute("""
        insert into block(user_pk, body_signature, body, is_release, create_time) 
        values (?,?,?,0,?)
        """, (user_pk, body_signature, str(body).encode("utf-8"), create_time))
        self.tempConn.commit()

    def saveBatchData(self, beings_list):
        create_time = STime.getTimestamp()
        cursor = self.tempConn.cursor()
        data_list = []
        for beings in beings_list:
            data_list.append(
                (beings["user_pk"], beings["body_signature"], str(beings["body"]).encode("utf-8"), create_time)
            )
        cursor.executemany("""
        insert into block(user_pk, body_signature, body, is_release, create_time) 
        values (?,?,?,0,?)
        """, data_list)
        self.tempConn.commit()

    def getTopData(self):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select id,user_pk,body_signature,body from block 
        where is_release = 0 limit 1
        """)
        res = cursor.fetchone()
        current_id = res[0]
        data = {
            "user_pk": res[1],
            "body_signature": res[2],
            "body": res[3]
        }
        cursor.execute("""
        update block set is_release = 1 where id = ?
        """, (current_id,))
        self.tempConn.commit()
        return data

    # 查询待发布的数据数量
    def getDataCount(self):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select count(*) from block where is_release = 0
        """)
        res = cursor.fetchone()
        data_count = res[0]
        return data_count

    # 查询待审核的新节点数量
    def getCountOfNodeApply(self):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select count(*) from node_join where is_audit = 0
        """)
        res = cursor.fetchone()
        data_count = res[0]
        return data_count

    def getNodeOfApplication(self, count) -> [ApplicationForm]:
        cursor = self.tempConn.cursor()
        res = cursor.execute("""
        select * from node_join where is_audit = 0 limit ?
        """, count)
        application_form_list = []
        for node in res:
            node_info = eval(bytes(node[1]).decode())
            nodeInfo = NodeInfo(node_id=node_info["node_id"], user_pk=node_info["user_pk"],
                                node_ip=node_info["node_ip"], create_time=node_info["create_time"])
            nodeInfo.nodeSignature = node[2]
            application = eval(bytes(node[3]).decode())

            application_form = ApplicationForm(db_id=node[0], node_info=nodeInfo, content=application["content"],
                                               new_node_signature=application["new_node_signature"])
            application_form_list.append(application_form)
        return application_form_list

    # 审核新节点请求
    def auditNodeOfApplication(self, db_id, is_audit, application, start_time=None, main_node_signature=None,
                               main_node_user_pk=None):
        application["start_time"] = start_time
        application["main_node_signature"] = main_node_signature
        application["main_node_user_pk"] = main_node_user_pk
        cursor = self.tempConn.cursor()
        cursor.execute("""
        update node_join 
        set is_audit= ?, application = ? 
        where id = ?  
        """, (is_audit, application, db_id))
        self.tempConn.commit()

    # 修改新节点的申请状态
    def modifyStateOfNewNode(self, db_id, is_audit):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        update node_join 
        set is_audit= ?
        where id = ?  
        """, (is_audit, db_id))
        self.tempConn.commit()

    def addVotes(self, vote_information: VoteInformation):
        user_pk = vote_information.userPK
        node_id = vote_information.mainNodeId
        election_period = vote_information.electionPeriod
        block_id = vote_information.blockId
        votes = vote_information.numberOfVote
        signature = vote_information.signature
        cursor = self.tempConn.cursor()
        cursor.execute("""
        insert into votes(election_period,node_id, block_id, user_pk, votes, signature,create_time)
        values (?,?,?,?,?,?,?)
        """, (election_period, node_id, block_id, user_pk, votes, signature, STime.getTimestamp()))
        self.tempConn.commit()

    # 返回该用户在该阶段已经使用的票数
    def getVotesByUserPk(self, user_pk, election_period) -> float:
        cursor = self.tempConn.cursor()
        res = cursor.execute("""
        select sum(votes) from votes
        where user_pk = ? and election_period = ?
        """, (user_pk, election_period))
        res = next(res)
        return res[0]

    # 判断该投票是否已经存在
    def voteIsExit(self, vote_information: VoteInformation):
        cursor = self.tempConn.cursor()
        res = cursor.execute("""
        select sum(id) from votes
        where node_id=? and election_period=? and block_id=? and user_pk = ? and votes = ?
        """, (
            vote_information.mainNodeId, vote_information.electionPeriod, vote_information.blockId,
            vote_information.userPK,
            vote_information.numberOfVote))
        res = next(res)
        if res[0] > 0:
            return True
        else:
            return False

    def getSimpleUserVoteByUserPk(self, user_pk, election_period):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select total_vote,used_vote from simple_user_vote where user_pk =? and election_period=?
        """, (user_pk, election_period))
        res = cursor.fetchone()
        if res is None:
            return 0.0
        else:
            return res[0] - res[1]


if __name__ == "__main__":
    s = StorageOfTemp()
    s.getSimpleUserVoteByUserPk(user_pk="sdsf", election_period=1)
