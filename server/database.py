import sqlite3
import time
from ast import literal_eval


class DB:
    def __init__(self):
        self.__backstageDB = sqlite3.connect('./db/backstage.db', check_same_thread=False)
        self.__initBackstageDB()
        self.__DB = sqlite3.connect('./db/database.db', check_same_thread=False)
        self.__initDB()

    def __initDB(self):
        cursor = self.__DB.cursor()
        # 用户提交的众生区块内容
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

        # 主动提交删除某节点的申请书
        cursor.execute("""select count(*) from sqlite_master 
        where type = 'table' and name = 'application_form_active_delete'""")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table application_form_active_delete(
            id INTEGER PRIMARY KEY,
            node_id TEXT NOT NULL,
            application_content TEXT NOT NULL,
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

        # 标记中的垃圾区块信息
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'garbage_block_queue'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table garbage_block_queue(
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

        # 存储授权给简单用户节点的票
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'simple_user_vote'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table simple_user_vote(
            id INTEGER PRIMARY KEY,
            election_period INTEGER NOT NULL,
            user_pk TEXT NOT NULL,
            total_vote FLOAT NOT NULL,
            used_vote FLOAT NOT NULL,
            update_time TEXT NOT NULL,
            create_time TEXT NOT NULL 
            )
            """)
            self.__DB.commit()

    def __initBackstageDB(self):
        cursor = self.__backstageDB.cursor()
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'users'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table users(
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            is_delete INTEGER NOT NULL,
            create_time TEXT NOT NULL
            )
            """)
            self.__backstageDB.commit()

        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'backstage_info'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table backstage_info(
            id INTEGER PRIMARY KEY,
            info_name TEXT NOT NULL,
            content TEXT NOT NULL,
            modify_time TEXT NOT NULL,
            create_time TEXT NOT NULL
            )
            """)
            self.__backstageDB.commit()

    def isUserExist(self, username) -> bool:
        cursor = self.__backstageDB.cursor()
        cursor.execute("""
        select count(*) from users
        where username = ?
        """, (username,))
        res = cursor.fetchone()
        if res[0] > 0:
            return True
        else:
            return False

    def addUser(self, username, password):
        cursor = self.__backstageDB.cursor()
        cursor.execute("""
        insert into users(username, password, is_delete, create_time) 
        values (?,?,?,?)
        """, (username, password, 0, time.time()))
        self.__backstageDB.commit()

    def updateUser(self, username, password):
        cursor = self.__backstageDB.cursor()
        cursor.execute("""
        update users set password = ?
        where username = ?
        """, (password, username))
        self.__backstageDB.commit()

    def verifyUsernameAndPassword(self, username, password) -> bool:
        cursor = self.__backstageDB.cursor()
        cursor.execute("""
        select count(*) from users where username = ? and password = ? and is_delete = 0
        """, (username, password))
        if cursor.fetchone()[0] > 0:
            return True
        else:
            return False

    def insertBlockOfBeings(self, user_pk, body: bytes, signature):
        cursor = self.__DB.cursor()
        cursor.execute("""
        insert into beings_block(user_pk,body,signature,is_review,create_time) values (?,?,?,?,?)
        """, (user_pk, body, signature, 0, time.time()))
        self.__DB.commit()

    def getBlockListOfBeings(self, count):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id,create_time from beings_block where is_review = 0 limit ?
        """, (count,))
        data_list = cursor.fetchall()
        id_list = []
        for data in data_list:
            id_list.append({
                "db_id": data[0],
                "create_time": data[1]
            })
        return id_list

    def getBlockListOfBeingsByOffset(self, offset, count):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id,create_time from beings_block where is_review = 0 and id >= ? limit ?
        """, (offset, count))
        data_list = cursor.fetchall()
        id_list = []
        for data in data_list:
            id_list.append({
                "db_id": data[0],
                "create_time": data[1]
            })
        return id_list

    def getWaitingBlockListOfBeingsByOffset(self, offset, count):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id,create_time from beings_block where is_review = 1 and id >= ? limit ?
        """, (offset, count))
        data_list = cursor.fetchall()
        id_list = []
        for data in data_list:
            id_list.append({
                "db_id": data[0],
                "create_time": data[1]
            })
        return id_list

    def getBlockOfBeingsByDBId(self, db_id):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select * from beings_block where id = ?
        """, (db_id,))
        res = cursor.fetchone()
        block = {
            "db_id": res[0],
            "user_pk": res[1],
            "body": bytes(res[2]).decode("utf-8"),
            "signature": res[3],
            "is_review": res[4],
            "review_username": res[5],
            "create_time": res[6]
        }
        return block

    def reviewBlockOfBeingsDBId(self, db_id, is_review):
        cursor = self.__DB.cursor()
        cursor.execute("""
        update beings_block set is_review = ?
        where id = ?
        """, (is_review, db_id))
        self.__DB.commit()

    # ############################# 申请成为主节点的申请书数据操作
    def insertApplicationForm(self, node_id, user_pk, node_ip, server_url, node_create_time, node_signature,
                              application, application_signature, remarks):
        cursor = self.__DB.cursor()
        cursor.execute("""
        insert into application_form(node_id, user_pk, node_ip,server_url, node_create_time, node_signature, application, 
        application_signature, is_review, remarks,create_time) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (node_id, user_pk, node_ip, server_url, node_create_time, node_signature, application,
              application_signature, 0, remarks, time.time()))
        self.__DB.commit()

    def getApplicationFormByOffset(self, offset, count):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id,create_time from application_form 
        where is_review = 0 and id > ? limit ?
        """, (offset, count))
        data_list = cursor.fetchall()
        id_list = []
        for data in data_list:
            id_list.append({
                "db_id": data[0],
                "create_time": data[1]
            })
        return id_list

    def getApplicationFormByDBId(self, db_id):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id, node_id, user_pk, node_ip, server_url,node_create_time, node_signature, application, 
        application_signature, is_review,remarks, create_time 
        from application_form where id = ?
        """, (db_id,))
        res = cursor.fetchone()
        application_form_dict = {
            "db_id": res[0],
            "node_id": res[1],
            "user_pk": res[2],
            "node_ip": res[3],
            "server_url": res[4],
            "node_create_time": res[5],
            "node_signature": res[6],
            "application": res[7],
            "application_signature": res[8],
            "is_review": res[9],
            "remarks": res[10],
            "create_time": res[11]
        }
        return application_form_dict

    def reviewApplicationFormByDBId(self, db_id, is_review):
        cursor = self.__DB.cursor()
        cursor.execute("""
        update application_form set is_review = ?
        where id = ?
        """, (is_review, db_id))
        self.__DB.commit()

    # ############################# 主动申请删除某主节点的申请书数据操作
    def getApplicationFormActiveDeleteOfBroadcastByOffset(self, offset, count):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id,create_time 
        from application_form_active_delete 
        where is_review = 1 and id > ? limit ?
        """, (offset, count))
        data_list = cursor.fetchall()
        id_list = []
        for data in data_list:
            id_list.append({
                "db_id": data[0],
                "create_time": data[1]
            })
        return id_list

    def insertApplicationFormActiveDelete(self, node_id, application_content, remarks):
        cursor = self.__DB.cursor()
        cursor.execute("""
        insert into application_form_active_delete(node_id,application_content,is_review, remarks,create_time) 
        VALUES (?,?,?,?,?)
        """, (node_id, application_content, 0, remarks, time.time()))
        self.__DB.commit()

    def getApplicationFormActiveDeleteByOffset(self, offset, count):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id,create_time from application_form_active_delete 
        where id > ? limit ?
        """, (offset, count))
        data_list = cursor.fetchall()
        id_list = []
        for data in data_list:
            id_list.append({
                "db_id": data[0],
                "create_time": data[1]
            })
        return id_list

    def getApplicationFormActiveDeleteByDBId(self, db_id):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id, node_id, application_content, is_review,remarks, create_time 
        from application_form_active_delete where id = ?
        """, (db_id,))
        res = cursor.fetchone()
        application_form_dict = {
            "db_id": res[0],
            "node_id": res[1],
            "application_content": res[2],
            "is_review": res[3],
            "remarks": res[4],
            "create_time": res[5]
        }
        return application_form_dict

    def getIndexNotice(self):
        cursor = self.__backstageDB.cursor()
        cursor.execute("""
        select id, info_name, content, modify_time, create_time from backstage_info
        where info_name = ?
        """, ("index_notice",))
        res = cursor.fetchone()
        if res is None:
            cursor.execute("""
            insert into backstage_info(info_name, content, modify_time, create_time) 
            values (?,?,?,?)
            """, ("index_notice", "", time.time(), time.time()))
            self.__backstageDB.commit()
            cursor.execute("""
            select id, info_name, content, modify_time, create_time from backstage_info
            where info_name = ?
            """, ("index_notice",))
            res = cursor.fetchone()
            return res
        else:
            return res

    def modifyIndexNotice(self, content):
        cursor = self.__backstageDB.cursor()
        cursor.execute("""
        update backstage_info 
        set content = ?, modify_time = ?
        where info_name = ?
        """, (content, time.time(), "index_notice"))
        self.__backstageDB.commit()
        cursor.execute("""
        select id, info_name, content, modify_time, create_time from backstage_info
        where info_name = ?
        """, ("index_notice",))
        res = cursor.fetchone()
        return res

    def insertTimesBlockQueue(self, election_period, beings_block_id, votes, vote_list):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select count(id) from times_block_queue
        where beings_block_id = ? and election_period = ?
        """, (beings_block_id, election_period))
        res = cursor.fetchone()
        if res[0] != 0:
            return False
        else:
            cursor.execute("""
            insert into times_block_queue(election_period, beings_block_id, votes, vote_list, status, create_time) 
            values (?,?,?,?,?,?)
            """, (election_period, beings_block_id, votes, str(vote_list).encode("utf-8"), 0, time.time()))
            self.__DB.commit()
            return True

    def modifyStatusOfTimesBlockQueue(self, beings_block_id, status):
        cursor = self.__DB.cursor()
        cursor.execute("""
        update times_block_queue
        set status = ?
        where beings_block_id = ?
        """, (status, beings_block_id))
        self.__DB.commit()

    def getListOfTimesBlockQueue(self, offset, count, election_period):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id, election_period, beings_block_id, votes from times_block_queue
        where status = 0 and election_period = ?
        order by id desc limit ?,?
        """, (election_period, offset, count))
        res = cursor.fetchall()
        res_list = []
        for data in res:
            res_list.append({
                "id": data[0],
                "election_period": data[1],
                "beings_block_id": data[2],
                "votes": data[3]
            })
        return res_list

    def getTimesBlockQueue(self, beings_block_id):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id, election_period, beings_block_id, votes, vote_list, status, create_time 
        from times_block_queue
        where beings_block_id = ?
        """, (beings_block_id,))
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

    def insertGarbageBlockQueue(self, election_period, beings_block_id, votes, vote_list):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select count(id) from garbage_block_queue
        where beings_block_id = ? and election_period = ?
        """, (beings_block_id, election_period))
        res = cursor.fetchone()
        if res[0] != 0:
            return False
        else:
            cursor.execute("""
            insert into garbage_block_queue(election_period, beings_block_id, votes, vote_list, status, create_time) 
            values (?,?,?,?,?,?)
            """, (election_period, beings_block_id, votes, str(vote_list).encode("utf-8"), 0, time.time()))
            self.__DB.commit()
            return True

    def modifyStatusOfGarbageBlockQueue(self, beings_block_id, status):
        cursor = self.__DB.cursor()
        cursor.execute("""
        update garbage_block_queue
        set status = ?
        where beings_block_id = ?
        """, (status, beings_block_id))
        self.__DB.commit()

    def getListOfGarbageBlockQueue(self, offset, count, election_period):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id, election_period, beings_block_id, votes 
        from garbage_block_queue
        where status = 0 and election_period = ?
        order by id desc limit ?,?
        """, (election_period, offset, count))
        res = cursor.fetchall()
        res_list = []
        for data in res:
            res_list.append({
                "id": data[0],
                "election_period": data[1],
                "beings_block_id": data[2],
                "votes": data[3]
            })
        return res_list

    def getGarbageBlockQueue(self, beings_block_id):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id, election_period, beings_block_id, votes, vote_list, status, create_time 
        from garbage_block_queue
        where beings_block_id = ?
        """, (beings_block_id,))
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

    # 获取备案号
    def getRecordNumber(self):
        cursor = self.__backstageDB.cursor()
        cursor.execute("""
        select id, info_name, content, modify_time, create_time from backstage_info
        where info_name = ?
        """, ("icp",))
        res = cursor.fetchone()
        if res is None:
            current_time = time.time()
            cursor.execute("""
            insert into backstage_info(info_name, content, modify_time, create_time)
            values (?,?,?,?)
            """, ("icp", "", current_time, current_time))
            self.__backstageDB.commit()
            return {
                "id": 0,
                "info_name": "icp",
                "content": "",
                "modify_time": current_time,
                "create_time": current_time,
            }
        else:
            return {
                "id": res[0],
                "info_name": res[1],
                "content": res[2],
                "modify_time": res[3],
                "create_time": res[4],
            }

    # 设置备案号
    def setRecordNumber(self, record_number):
        cursor = self.__backstageDB.cursor()
        cursor.execute("""
        update backstage_info 
        set content = ?
        where info_name = ?
        """, (record_number, "icp"))
        self.__backstageDB.commit()
        cursor.execute("""
        select id, info_name, content, modify_time, create_time from backstage_info
        where info_name = ?
        """, ("icp",))
        res = cursor.fetchone()
        return {
            "id": res[0],
            "info_name": res[1],
            "content": res[2],
            "modify_time": res[3],
            "create_time": res[4],
        }

    def addSimpleUserVote(self, election_period, user_pk, total_vote):
        cursor = self.__DB.cursor()
        create_time = time.time()
        cursor.execute("""
        insert into simple_user_vote(election_period, user_pk, total_vote, used_vote, update_time,create_time)
        values (?,?,?,?,?,?)
        """, (election_period, user_pk, total_vote, 0, create_time, create_time))
        self.__DB.commit()

    def clearSimpleUserVote(self):
        cursor = self.__DB.cursor()
        cursor.execute("""
        delete from simple_user_vote
        """)
        self.__DB.commit()

    def getListOfSimpleUserVote(self, offset, count, election_period):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select user_pk from simple_user_vote
        where id >= ? and id < ? and election_period = ?
        """, (offset, count, election_period))
        res = cursor.fetchall()
        user_pk_list = []
        for data in res:
            user_pk_list.append(data[0])
        return user_pk_list

    def getSimpleUserVoteByUserPk(self, user_pk, election_period):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id, election_period, user_pk, total_vote, used_vote, update_time, create_time 
        from simple_user_vote
        where user_pk = ? and election_period = ?
        """, (user_pk, election_period))
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

    def addUsedVoteOfSimpleUser(self, user_pk, used_vote, election_period):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select used_vote from simple_user_vote
        where user_pk = ? and election_period = ?
        """, (user_pk, election_period))
        res = cursor.fetchone()
        if res is not None:
            original_used_vote = round(res[0], 1)
            cursor.execute("""
            update simple_user_vote 
            set used_vote = ?
            where user_pk = ? and election_period = ?
            """, (round(used_vote, 1) + original_used_vote, user_pk, election_period))
            self.__DB.commit()
            return self.getSimpleUserVoteByUserPk(user_pk, election_period)
        else:
            return None

    def modifyTotalVoteOfSimpleUser(self, user_pk, total_vote, election_period) -> bool:
        data = self.getSimpleUserVoteByUserPk(user_pk, election_period)
        if data is None:
            return False
        used_vote = data["used_vote"]
        if total_vote < used_vote:
            return False
        cursor = self.__DB.cursor()
        cursor.execute("""
        update simple_user_vote
        set total_vote = ?
        where user_pk = ?
        """, (float(total_vote), user_pk))
        self.__DB.commit()
        return True


if __name__ == "__main__":
    DB()
