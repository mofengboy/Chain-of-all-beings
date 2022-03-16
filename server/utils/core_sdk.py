import sqlite3


class DBOfTemp:
    def __init__(self):
        self.tempConn = sqlite3.connect('../core/db/temp.db', check_same_thread=False)

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
        select id, node_id, user_pk, node_ip, node_create_time, 
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
