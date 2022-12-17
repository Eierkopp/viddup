#!/usr/bin/python3
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
import argparse
from itertools import combinations
import logging
import psycopg
from tqdm import tqdm
from typing import Iterable, List, Any

from viddup import DB
from .tools import NCOLS


class Index(ABC):

    def __init__(self, dbi: DB, params: argparse.Namespace):
        self.dbi = dbi
        self.params = params
        with dbi.getconn() as conn:
            self.init_index(conn)

    def search(self, conn: psycopg.Connection) -> List[List[List[Any]]]:
        logging.info("Searching duplicates")
        radius = self.params.radius
        step = self.params.step
        debug = self.params.debug
        data_length = self.idx_get_length()

        known_duplicates = set()
        result = []

        for i in tqdm(range(0, data_length, step), ascii=True, ncols=NCOLS):
            elem_idx = self.idx_get_nn(i, radius)
            elem_idx.sort()
            if len(elem_idx) > 1:
                details = []

                fids: List[int] = [self.fi_list[i].fid for i in elem_idx]
                fids.sort()

                pairs = list(combinations(fids, 2))

                for pair in pairs[:]:
                    if pair[0] == pair[1] or pair in known_duplicates or self.is_whitelisted(conn, pair):
                        known_duplicates.add(pair)
                        pairs.remove(pair)
                fid_pairs = set(i[0] for i in pairs).union(i[1] for i in pairs)
                if not fid_pairs:
                    continue

                known_duplicates.update(set(pairs))
                known_fids = set()
                for n, item in enumerate(elem_idx):
                    try:
                        fid = self.fi_list[item].fid
                        if fid not in fids or fid in known_fids:
                            continue
                        known_fids.add(fid)
                        fileinfo, frame = self.fi_list[item], self.frame_list[item]
                        if debug:
                            logging.info("%4d, %-50s: %s",
                                         fileinfo.fid,
                                         fileinfo.name[-50:],
                                         self.idx_get_row(item))
                        details.append([fileinfo, frame/fileinfo.fps])
                    except KeyboardInterrupt:
                        raise
                    except Exception:
                        logging.info("Error processing: %s, purge required?", item, exc_info=True)
                if len(details) > 1:
                    result.append(details)
        return result

    def is_whitelisted(self, conn: psycopg.Connection, ids: Iterable[int]) -> bool:
        """Return True, if all pairs of filenames are whitelisted"""
        for id1, id2 in combinations(ids, 2):
            if not self.dbi.is_whitelisted(conn, id1, id2):
                return False
        return True

    def init_index(self, conn: psycopg.Connection) -> None:
        logging.info("Loading hashes")
        self.fi_list = []    # fileinfo for item
        self.frame_list = []  # first frame for item
        items = []

        index_length = self.params.indexlength
        scene_seconds = self.params.scenelength
        ignore_start = self.params.ignore_start
        ignore_end = self.params.ignore_end

        with tqdm(self.dbi.get_file_infos(conn), ascii=True, ncols=NCOLS) as progress_bar:
            for fileinfo in progress_bar:
                min_frame = int(ignore_start * fileinfo.fps)
                max_frame = int((fileinfo.duration - ignore_end) * fileinfo.fps)

                frames, hashes = self.dbi.get_hashes(conn, fileinfo.fid, min_frame, max_frame)
                if len(hashes) < 5:  # ignore fid, if list of hashes is too short
                    continue

                item_count = max(0, len(hashes) - index_length)

                for i in range(item_count):
                    item = hashes[i:i+index_length]
                    total_time = 0.0
                    for n, v in enumerate(item):
                        if total_time > scene_seconds:
                            item[n] = 0.0
                        total_time += v
                    items.append(item)
                    self.fi_list.append(fileinfo)
                    self.frame_list.append(frames[i])

        self.mk_index(items)

    @abstractmethod
    def mk_index(self, items: List[List[float]]) -> None:
        pass

    @abstractmethod
    def idx_get_length(self) -> int:
        return 0

    @abstractmethod
    def idx_get_nn(self, rownum: int, radius: float) -> List[int]:
        return list()

    @abstractmethod
    def idx_get_row(self, rownum: int) -> List[float]:
        pass
