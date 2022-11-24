#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
from collections import namedtuple
from itertools import combinations
import logging
import os
import time
from typing import List, Optional
from tqdm import tqdm

from viddup import DB

NCOLS = 70


class TqdmStream:

    def __init__(self, stream):
        self.stream = stream

    def write(self, data: str) -> None:
        data = data.rstrip("\r\n")
        if data:
            tqdm.write(data, file=self.stream)
            self.stream.flush()


def format_duration(seconds: float) -> str:
    return time.strftime("%H:%M:%S", time.gmtime(seconds))


def whitelist(dbi: DB, params: argparse.Namespace, files: Optional[List[str]] = None) -> None:

    Entry = namedtuple("Entry", "name, fid")

    if files is None:
        files = params.whitelist

    with dbi.getconn() as conn:
        ids = set()
        for f in files:
            fid = dbi.get_id(conn, f)
            if fid is not None:
                ids.add(Entry._make([f, fid]))
            else:
                logging.warn("File %s not found in DB", f)

        if len(ids) < 2:
            logging.warning("Need at least two files to whitelist")
            return

        for f1, f2 in combinations(list(ids), 2):
            try:
                dbi.whitelist(conn, f1.fid, f2.fid)
                logging.info("Whitelisted %s and %s" % (f1.name, f2.name))
                conn.commit()
            except Exception:
                logging.error("Failed to whitelist pair %s - %s", f1.name, f2.name, exc_info=False)
                conn.rollback()


def handle_purge(dbi: DB, params: argparse.Namespace, do_delete: Optional[bool] = None) -> None:

    if do_delete is None:
        do_delete = params.delete

    with dbi.getconn() as conn:

        dbi.tidy_db(conn)

        del_files = []
        fn_fis = []
        for fi in dbi.get_file_infos(conn):
            fn_fis.append(fi.fid)
            if not os.access(fi.name, os.R_OK):
                del_files.append(fi)

        logging.warning("Need to delete %d of %d files",
                        len(del_files),
                        len(fn_fis))
        if do_delete:
            for fi in del_files:
                logging.info("deleting %s", fi.name)
                dbi.del_file(conn, fi.fid)
        else:
            for fi in del_files:
                logging.info(fi.name)
        conn.commit()
