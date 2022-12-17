#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import multiprocessing
from typing import List

import hnswlib
import numpy as np

from .index import Index


class HnswlibIndex(Index):

    def mk_index(self, items: List[List[float]]) -> None:
        logging.info("Start building hnswlib index")
        index_length = self.params.indexlength
        self.idx = hnswlib.Index(space='l2', dim=index_length)
        self.idx.set_num_threads(multiprocessing.cpu_count())
        self.idx.init_index(max_elements=len(items), ef_construction=100, M=index_length)
        np_items = np.array(items, dtype="float64")
        if self.params.fixspeed:
            for n, item in enumerate(np_items):
                np_items[n] = 128.0*item/np.mean(item)

        self.idx.add_items(np_items)
        self.__items = np_items

    def idx_get_length(self) -> int:
        return len(self.__items)

    def idx_get_nn(self, rownum: int, radius: float) -> List[int]:
        result = []
        elem_idx, elem_dists = self.idx.knn_query(self.__items[rownum], k=20)
        for n, item in enumerate(elem_idx[0]):
            if elem_dists[0][n] < radius:
                result.append(item)
        return result

    def idx_get_row(self, rownum: int) -> List[float]:
        return self.__items[rownum]
