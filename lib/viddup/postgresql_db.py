#!/usr/bin/python3
# -*- coding: utf-8 -*-

from argparse import Namespace
from collections import namedtuple
from contextlib import contextmanager
import logging
from typing import List, Tuple, Generator, Optional
from psycopg import Connection
from psycopg_pool import ConnectionPool

FileInfo = namedtuple("FileInfo", "fid, name, fps, duration")


class DB:

    def __init__(self, params: Namespace):
        self.params = params
        database = self.params.dbname
        host = self.params.dbhost
        port = self.params.dbport
        user = self.params.dbuser
        password = self.params.dbpwd
        self.pool = ConnectionPool(f"postgresql://{user}:{password}@{host}:{port}/{database}")
        self.make_schema()

    @contextmanager
    def getconn(self, policy: str = "rollback") -> Generator[Connection, None, None]:
        committed = False
        try:
            conn = self.pool.getconn()
            yield conn
        except Exception:
            conn.rollback()
            committed = True
            raise
        finally:
            if not committed:
                getattr(conn, policy)()
            self.pool.putconn(conn)

    def make_schema(self) -> None:
        """Create the database schema if it does not exist already"""

        logging.info("Asserting DB schema is up-to-date")
        with self.getconn() as conn:
            with conn.cursor() as c:
                c.execute("create table if not exists filenames "
                          "(id serial primary key,"
                          " name text not null,"
                          " fps float not null,"
                          " duration float not null)")
                c.execute("create unique index if not exists filenames_name_ux on filenames (name)")
                c.execute("create table if not exists hashes "
                          "(filename_id integer not null references filenames(id) on delete cascade,"
                          " frame integer not null,"
                          " hash float not null,"
                          " primary key (filename_id, frame))")
                c.execute("create table if not exists brightness "
                          "(filename_id integer not null references filenames(id) on delete cascade,"
                          " brightness float[],"
                          " primary key (filename_id))")
                c.execute("create table if not exists whitelist "
                          "(id1 integer not null references filenames(id) on delete cascade,"
                          " id2 integer not null references filenames(id) on delete cascade,"
                          " primary key (id1, id2))")
            conn.commit()

    def is_name_in_db(self, conn, fname: str) -> bool:
        fid = self.get_id(conn, fname)
        return fid is not None

    def get_id(self, conn: Connection, fname: str) -> Optional[int]:
        with conn.cursor() as c:
            c.execute("select id from filenames where name=%s", [fname])
            rs = c.fetchall()
            if len(rs) == 0:
                return None
            else:
                fid, = rs[0]
                return fid

    def del_file(self, conn: Connection, fid: int) -> None:
        with conn.cursor() as c:
            c.execute("delete from filenames where id=%s", [fid])

    def insert_brightness(self, conn: Connection, fid: int, brightness: List[float]) -> None:
        with conn.cursor() as c:
            c.execute("delete from brightness where filename_id = %s", [fid])
            c.execute("insert into brightness (filename_id, brightness) values (%s, %s)", [fid, brightness])

    def get_brightness(self, conn: Connection, fid: int) -> List[float]:
        c = conn.execute("select brightness from brightness where filename_id = %s", [fid])
        data = c.fetchone()
        if data:
            return data[0]
        else:
            return []

    def get_file_infos(self, conn: Connection) -> List[FileInfo]:
        with conn.cursor() as c:
            c.execute("select id, name, fps, duration from filenames order by id asc")
            return [FileInfo._make(i) for i in c.fetchall()]

    def insert_file(self, conn: Connection, fname: str, fps: float, duration: float) -> FileInfo:
        fid = self.get_id(conn, fname)
        if fid is None:
            with conn.cursor() as c:
                c.execute("insert into filenames (name, fps, duration) "
                          " values (%s, %s, %s) returning id", [fname, fps, duration])
                result = c.fetchone()
                fid = result[0] if result is not None else None
        else:
            with conn.cursor() as c:
                c.execute("update filenames set name=%s, fps=%s, duration=%s where id=%s", [fname, fps, duration, fid])
        return FileInfo(fid, fname, fps, duration)

    def insert_hashes(self, conn: Connection, fid: int, index_info: List[Tuple[int, float]]) -> None:
        with conn.cursor() as c:
            c.execute("delete from hashes where filename_id = %s", [fid])
            for f, h in index_info:
                c.execute("insert into hashes (filename_id, frame, hash) values (%s, %s, %s)", [fid, f, h])

    def update_name(self, conn: Connection, fid: int, name: str) -> None:
        with conn.cursor() as c:
            c.execute("update filenames set name=%s where id=%s", [name, fid])

    def tidy_db(self, conn: Connection) -> None:
        logging.info("Cleaning DB")
        with conn.cursor() as c:
            c.execute("delete from filenames where not exists (select 1 from hashes where filename_id = id limit 1)")

    def get_hashes(self, conn: Connection, fid: int, min_frame: int, max_frame: int) -> Tuple[List[int], List[float]]:
        with conn.cursor() as c:
            c.execute("select frame, hash from hashes "
                      " where filename_id = %s and frame >= %s and frame <= %s order by frame",
                      [fid, min_frame, max_frame])
            result = c.fetchall()
        frames = [p[0] for p in result]
        hashes = [p[1] for p in result]
        return frames, hashes

    def has_hashes(self, conn: Connection, fid: int) -> bool:
        with conn.cursor() as c:
            c.execute("select frame from hashes where filename_id = %s limit 1", [fid])
            return len(c.fetchall()) > 0

    def is_whitelisted(self, conn: Connection, id1: int, id2: int) -> bool:
        if id1 > id2:
            id1, id2 = id2, id1
        with conn.cursor() as c:
            c.execute("select 1 from whitelist where id1 = %s and id2 = %s", [id1, id2])
            return len(c.fetchall()) > 0

    def whitelist(self, conn: Connection, id1: int, id2: int) -> None:
        if id1 > id2:
            id1, id2 = id2, id1
        with conn.cursor() as c:
            c.execute("insert into whitelist (id1, id2) values (%s, %s)", [id1, id2])
