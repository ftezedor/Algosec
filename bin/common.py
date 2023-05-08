import getpass
from inspect import isfunction
import sys, io
import time
import sqlite3
import base64 as b64

#from sqlite3 import Error

class MissingArgumentError(RuntimeError):
    pass

class MissingDataError(RuntimeError):
    pass

class UnknownFormatError(RuntimeError):
    pass

class Input:
    @staticmethod
    def gettext(prompt: str = "enter text: ", default: str = ""):
        """
        Args:
          prompt: message to display while asking for imput
          default: default value to return if none is entered
        Returns:
          default or entered value
        """
        retval = raw_input(prompt) if isfunction("raw_input") else input(prompt)

        #if not isfunction("raw_input"):
        #    retval = input(msg)
        #else:
        #    retval = raw_input(msg)
        if retval is None or retval == '':
            return default
        
        return retval

    @staticmethod
    def getpass(msg: str = "enter password: "):
        return getpass.getpass(msg)

class B64:
    @staticmethod
    def encode(msg):
        b_msg = msg.encode("ascii")
        b_msg = b64.b64encode(b_msg)
        return b_msg.decode("ascii")

    @staticmethod
    def decode(msg):
        b_msg = msg.encode("ascii")
        b_msg = b64.b64decode(b_msg)
        return b_msg.decode("ascii")

class HEX:
    @staticmethod
    def encode(msg):
        return msg.encode("utf-8").hex()

    @staticmethod
    def decode(hex):
        if hex[:2] == "0x":
            hex = hex[2:]
        return bytes.fromhex(hex).decode("utf-8")



class Printer(io.IOBase):
    def write(self, str):
        sys.stdout.write(str)

    def close(self):
        pass

class Record():
    def __init__(self):
        self.requestId = 0
        self.questionId = 0
        self.questionNumber = 0
        self.hostname = ''
        self.questionType = 'unknown'

class Database():
    def __init__(self):
        self.__db = sqlite3.connect("tufin.db")
        # create tables
        sql = "CREATE TABLE IF NOT EXISTS rules (id text NOT NULL, source text NOT NULL, target text NOT NULL, protocol text NOT NULL);"
        self.__db.execute(sql)

    def __enter__(self):
        return self

    def __del__(self):
        print("closing database connection")
        self.__db.commit()
        self.__db.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def add_rule(self, rid, src, tgt, ptcl):
        #print("{}, {}, {}, {}".format(rid, src, tgt, ptcl))
        sql = "INSERT INTO rules (id, source, target, protocol) values (?, ?, ?, ?)"
        self.__db.execute( sql, (rid, src, tgt, ptcl) ).close()

    def get_all_sources(self):
        sql = "select source, count(source) items from rules group by source"
        cur = self.__db.execute( sql )
        data = cur.fetchall()
        cur.close()
        return data



def default(s, d):
    if type(s) != str or s is None or s == "":
        return d
    return s

class ToolBox:
    @staticmethod
    def iif(cond, true, false):
        return true if cond else false

class Timer:
    def __init__(self):
        self._start = time.time()
    
    def start(self):
        self._start = time.time()

    def stop(self):
        self._stop = time.time()

    def elapsed(self) -> float:
        return self._stop - self._start