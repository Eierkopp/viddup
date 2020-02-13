import logging
from .db_common import FileInfo

__all__ = ["get_db", "FileInfo"]


def get_db(params):

    if params.db:  # use SQLITE3 DB
        logging.info("Using Sqlite3")
        from .sqlite3_db import DB
    else:  # use PostgreSQL
        logging.info("Using PostgreSQL")
        from .postgresql_db import DB

    return DB(params)
