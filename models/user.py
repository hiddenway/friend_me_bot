import datetime
import sqlite3

class User:
    
    def __init__(self, chat_id, username, ref_id=None):
        self.chat_id = chat_id
        self.username = username
        self.ref_id = ref_id

        self.connect = sqlite3.connect('friendMe.db', check_same_thread=False)
    
    def auth(self):
        cursor = self.connect.cursor()
        cursor.execute("SELECT tg_id FROM users WHERE tg_id=?", (self.chat_id,))
        data = cursor.fetchone()

        if data is None:
            cursor.execute("INSERT INTO users VALUES(?,?,?,?,?);", (None, self.chat_id, self.username, self.ref_id, datetime.datetime.now()))
            self.connect.commit()

        else:
            if self.ref_id is not None:
                cursor.execute("UPDATE users SET ref_id=? WHERE tg_id=?", (self.ref_id, self.chat_id))
                self.connect.commit()

        cursor.execute("SELECT * FROM users WHERE tg_id=?", (self.chat_id, ))
        User = cursor.fetchone()

        print("User Data: ", User)

        return User