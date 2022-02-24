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
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'beings'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table beings(
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
        insert into beings(user_pk,body,signature,is_review,create_time) values (?,?,?,0,?)
        """, (user_pk, body, signature, time.time()))
        self.__DB.commit()

    def getBlockListOfBeings(self, count):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id,create_time from beings where is_review = 0 limit ?
        """, (count,))
        data_list = cursor.fetchall()
        id_list = []
        for data in data_list:
            id_list.append({
                "db_id": data[0],
                "crate_time": data[1]
            })
        return id_list

    def getBlockOfBeingsByDBId(self, db_id):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select * from beings where id = ?
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

    def reviewBlockOfBeingsDBId(self, db_id, is_review, review_username):
        cursor = self.__DB.cursor()
        cursor.execute("""
        update beings set is_review=?,review_username=?
        where id = ?
        """, (is_review, review_username, db_id))
        self.__DB.commit()
