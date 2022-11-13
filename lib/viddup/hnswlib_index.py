#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import multiprocessing

import hnswlib
import numpy as np

from .index import Index


class HnswlibIndex(Index):

    def mk_index(self, items):
        logging.info("Start building hnswlib index")
        index_length = self.params.indexlength
        self.idx = hnswlib.Index(space='l2', dim=index_length)
        self.idx.set_num_threads(multiprocessing.cpu_count())
        self.idx.init_index(max_elements=len(items), ef_construction=100, M=index_length)
        items = np.array(items)
        if self.params.fixspeed:
            for n, item in enumerate(items):
                items[n] = 128.0*item/np.mean(item)

        self.idx.add_items(items)
        self.__items = items

    def idx_get_length(self):
        return len(self.__items)

    def idx_get_nn(self, rownum, radius):
        result = []
        elem_idx, elem_dists = self.idx.knn_query(self.__items[rownum], k=20)
        for n, item in enumerate(elem_idx[0]):
            if elem_dists[0][n] < radius:
                result.append(item)
        return result

    def idx_get_row(self, rownum):
        return self.__items[rownum]
