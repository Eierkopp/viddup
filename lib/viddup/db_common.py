from contextlib import contextmanager
from collections import namedtuple

FileInfo = namedtuple("FileInfo", "fid, name, fps, duration")


def mk_stmt(db_mod):

    statements = {
        "TIDY_FILENAMES": ("delete from filenames where not exists ("
                           "select 1 from hashes where filename_id = id limit 1)"),
        "IS_WHITELISTED": "select 1 from whitelist where id1 = %% and id2 = %%",
        "GET_HASHES": ("select frame, hash from hashes "
                       " where filename_id = %% and frame >= %% and frame <= %% order by frame"),
        "INSERT_HASHES": "insert into hashes (filename_id, frame, hash) values (%%, %%, %%)",
        "DELETE_HASHES": "delete from hashes where filename_id = %%",
        "DELETE_BRIGHTNESS": "delete from brightness where filename_id = %%",
        "INSERT_BRIGHTNESS": "insert into brightness (filename_id, brightness) values (%%, %%)",
        "GET_BRIGHTNESS": "select brightness from brightness where filename_id = %%",
        "UPDATE_FILE": "update filenames set name=%%, fps=%%, duration=%% where id=%%",
        "GET_FILE_ID": "select id from filenames where name=%%",
        "DEL_FILE": "delete from filenames where id=%%",
        "INSERT_WHITELIST": "insert into whitelist values (%%,%%)",
        "FILE_INFOS": "select id, name, fps, duration from filenames order by id asc",
        }

    if db_mod.paramstyle == "qmark":
        repl = "?"
    elif db_mod.paramstyle == "pyformat":
        repl = "%s"
    else:
        raise Exception("unsupported db module")

    for key, value in statements.items():
        statements[key] = value.replace("%%", repl)

    return statements


class DBBase(object):

    def __init__(self, params):
        self.params = params
        self.s = self.init_statements()
        self.conn = self.get_db()
        self.make_schema()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    @contextmanager
    def transaction(self, policy="collback"):
        yield self.conn
        self.rollback() if policy == "rollback" else self.commit()

    def is_name_in_db(self, fname):
        fid = self.get_id(fname)
        return fid is not None

    def get_id(self, fname):
        with self.cursor() as c:
            c.execute(self.s["GET_FILE_ID"], [fname])
            rs = c.fetchall()
            if len(rs) == 0:
                return None
            else:
                fid, = rs[0]
                return fid

    def get_file_infos(self):
        with self.cursor() as c:
            c.execute(self.s["FILE_INFOS"])
            return [FileInfo._make(i) for i in c.fetchall()]

    def insert_hashes(self, fid, index_info):
        with self.cursor() as c:
            c.execute(self.s["DELETE_HASHES"], [fid])
            for f, h in index_info:
                c.execute(self.s["INSERT_HASHES"], [fid, f, h])

    def get_hashes(self, fid, min_frame, max_frame):
        with self.cursor() as c:
            c.execute(self.s["GET_HASHES"], [fid, min_frame, max_frame])
            result = c.fetchall()
        frames = [p[0] for p in result]
        hashes = [p[1] for p in result]
        return frames, hashes

    def is_whitelisted(self, id1, id2):
        if id1 > id2:
            id1, id2 = id2, id1
        with self.cursor() as c:
            c.execute(self.s["IS_WHITELISTED"], [id1, id2])
            return len(c.fetchall()) > 0

    def whitelist(self, id1, id2):
        if id1 > id2:
            id1, id2 = id2, id1
        with self.cursor() as c:
            c.execute(self.s["INSERT_WHITELIST"], [id1, id2])
