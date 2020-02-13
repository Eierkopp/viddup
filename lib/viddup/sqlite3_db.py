#!/usr/bin/python3

from contextlib import contextmanager
import logging
import sqlite3 as sq
import json

from .db_common import FileInfo, mk_stmt, DBBase


class DB(DBBase):

    def init_statements(self):
        return mk_stmt(sq)

    def get_db(self):
        conn = sq.connect(self.params.db)
        conn.execute("pragma busy_timeout = 300000").close()
        return conn

    @contextmanager
    def cursor(self):
        c = self.conn.cursor()
        try:
            yield c
        finally:
            c.close()

    def make_schema(self):
        """Create the database schema if it does not exist already"""

        logging.info("Asserting DB schema is up-to-date")
        with self.cursor() as c:
            c.execute("create table if not exists filenames "
                      "(id INTEGER PRIMARY KEY, "
                      " name text, "
                      " fps float, "
                      " duration float)")
            c.execute("create unique index if not exists name_ux on filenames (name)")
            c.execute("create table if not exists hashes "
                      "(filename_id int64, "
                      " frame int, "
                      " hash float)")
            c.execute("create table if not exists whitelist "
                      "(id1 INTEGER, "
                      " id2 INTEGER)")
            c.execute("create table if not exists brightness "
                      "(filename_id int64, "
                      " brightness blob)")
            c.execute("create unique index if not exists whitelist_ux on whitelist (id1, id2)")
            c.execute("create unique index if not exists filename_id_hashes_ux on hashes "
                      "(filename_id, frame)")
            c.execute("create index if not exists brightness_fid_idx on brightness (filename_id)")

    def del_file(self, fid):
        with self.cursor() as c:
            c.execute(self.s["DEL_FILE"], [fid])
            c.execute("delete from hashes where filename_id = ?", [fid])
            c.execute("delete from brightness where filename_id = ?", [fid])
            c.execute("delete from whitelist where id1 = ? or id2 = ?", [fid, fid])
        self.conn.commit()

    def insert_brightness(self, fid, brightness):
        with self.cursor() as c:
            c.execute(self.s["DELETE_BRIGHTNESS"], [fid])
            c.execute(self.s["INSERT_BRIGHTNESS"], [fid, json.dumps(brightness)])

    def get_brightness(self, fid):
        with self.cursor() as c:
            c.execute(self.s["GET_BRIGHTNESS"], [fid])
            return json.loads(c.fetchone()[0])

    def insert_file(self, fname, fps, duration):
        fid = self.get_id(fname)
        if fid is None:
            with self.cursor() as c:
                c.execute("insert into filenames values (null, ?, ?, ?)", [fname, fps, duration])
                fid = c.lastrowid
        else:
            with self.cursor() as c:
                c.execute(self.s["UPDATE_FILE"], [fname, fps, duration, fid])
        return FileInfo(fid, fname, fps, duration)

    def tidy_db(self):
        logging.info("Cleaning DB")
        try:
            with self.cursor() as c:
                c.execute(self.self.s["TIDY_FILENAMES"])
                c.execute("delete from hashes where filename_id not in (select id from filenames)")
                c.execute("delete from brightness "
                          "where filename_id not in (select id from  filenames)")
                c.execute("delete from whitelist where id1 not in (select id from filenames)")
                c.execute("delete from whitelist where id2 not in (select id from filenames)")
            self.conn.commit()
        except Exception as e:
            logging("Error during cleaning up: %s", e, exc_info=True)
            self.conn.rollback()
