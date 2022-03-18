import sqlite3


# web server数据库
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
            create_time TEXT NOT NULL
            )
            """)
            self.__DB.commit()

    def getWaitingBlockListOfBeingsToSDK(self):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id,user_pk,body,signature,is_review,review_username,create_time 
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
                "review_username": data[5],
                "create_time": data[6]
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
        select id, node_id, user_pk, node_ip, node_create_time, node_signature, 
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
                "node_create_time": data[4],
                "node_signature": data[5],
                "application": data[6],
                "application_signature": data[7],
                "is_review": data[8],
                "create_time": data[9]
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
                "node_id": data[1],
                "user_pk": data[2],
                "node_ip": data[3],
                "node_create_time": data[4],
                "node_signature": data[5],
                "application": data[6],
                "application_time": data[7],
                "application_signature": data[8]
            })
        return application_form_list

    def getApplicationFormCount(self):
        return self.db.getWaitingApplicationFormCountToSDK()
