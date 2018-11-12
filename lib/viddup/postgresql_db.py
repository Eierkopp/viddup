#!/usr/bin/python3

import logging
import psycopg2 as pg

from .db_common import FileInfo, mk_stmt, DBBase

class DB(DBBase):

    def init_statements(self):
        return mk_stmt(pg)

    def get_db(self):
        return pg.connect("host=%s port=%d dbname=%s user=%s password=%s" % (self.params.dbhost, self.params.dbport, self.params.dbname, self.params.dbuser, self.params.dbpwd))

    def cursor(self):
        return self.conn.cursor()

    def make_schema(self):
        """Create the database schema if it does not exist already"""

        logging.info("Asserting DB schema is up-to-date")
        with self.cursor() as c:
            c.execute("create table if not exists filenames (id serial primary key, name text not null, fps float not null, duration float not null)")
            c.execute("create unique index if not exists filenames_name_ux on filenames (name)")
            c.execute("""create table if not exists hashes 
                           (filename_id integer not null references filenames(id) on delete cascade,
                            frame integer not null, 
                            hash float not null, 
                            primary key (filename_id, frame))""")
            c.execute("""create table if not exists brightness 
                           (filename_id integer not null references filenames(id) on delete cascade, 
                            brightness float[], 
                            primary key (filename_id))""")
            c.execute("""create table if not exists whitelist 
                           (id1 integer not null references filenames(id) on delete cascade, 
                            id2 integer not null references filenames(id) on delete cascade,
                            primary key (id1, id2))""")
            print("anton")

    def del_file(self, fid):
        with self.cursor() as c:
            c.execute(self.s["DEL_FILE"], [fid])
        self.conn.commit()

    def insert_brightness(self, fid, brightness):
        with self.cursor() as c:
            c.execute(self.s["DELETE_BRIGHTNESS"], [fid])
            c.execute(self.s["INSERT_BRIGHTNESS"], [fid, brightness])

    def insert_file(self, fname, fps, duration):
        fid = self.get_id(fname)
        if fid is None:
            with self.cursor() as c:
                c.execute("insert into filenames (name, fps, duration) values (%s, %s, %s) returning id", [fname, fps, duration])
                fid, = c.fetchone()
        else:
            with cursor(conn) as c:
                c.execute(self.s["UPDATE_FILE"], [fname, fps, duration, fid])
        return FileInfo(fid, fname, fps, duration)

    def tidy_db(self):
        logging.info("Cleaning DB")
        try:
            with self.cursor() as c:
                c.execute(self.s["TIDY_FILENAMES"]);
            self.conn.commit()
        except Exception as e:
            logging("Error during cleaning up: %s", e, exc_info=True)
            self.conn.rollback()
