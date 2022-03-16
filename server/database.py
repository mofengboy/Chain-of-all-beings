import sqlite3
import time


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

    def insertBlockOfBeings(self, user_pk, body, signature):
        cursor = self.__DB.cursor()
        cursor.execute("""
        insert into beings_block(user_pk,body,signature,is_review,create_time) values (?,?,?,0,?)
        """, (user_pk, body, signature, time.time()))
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

    def insertApplicationForm(self, node_id, user_pk, node_ip, node_create_time, node_signature, application,
                              application_signature, remarks):
        cursor = self.__DB.cursor()
        cursor.execute("""
        insert into application_form(node_id, user_pk, node_ip, node_create_time, node_signature, application, 
        application_signature, is_review, remarks,create_time) 
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (node_id, user_pk, node_ip, node_create_time, node_signature, application,
              application_signature, 0, remarks, time.time()))
        self.__DB.commit()

    def getApplicationFormByOffset(self, offset, count):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id,create_time from application_form where is_review = 0 and id> ? limit ?
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
        select id, node_id, user_pk, node_ip, node_create_time, node_signature, application, 
        application_signature, is_review,remarks, create_time 
        from application_form where id = ?
        """, (db_id,))
        res = cursor.fetchone()
        application_form_dict = {
            "db_id": res[0],
            "node_id": res[1],
            "user_pk": res[2],
            "node_ip": res[3],
            "node_create_time": res[4],
            "node_signature": res[5],
            "application": res[6],
            "application_signature": res[7],
            "is_review": res[8],
            "remarks": res[9],
            "create_time": res[10]
        }
        return application_form_dict

    def reviewApplicationFormByDBId(self, db_id, is_review):
        cursor = self.__DB.cursor()
        cursor.execute("""
        update application_form set is_review = ?
        where id = ?
        """, (is_review, db_id))
        self.__DB.commit()


if __name__ == "__main__":
    DB()
