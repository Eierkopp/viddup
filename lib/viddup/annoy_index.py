#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging

import annoy
import numpy as np

from .index import Index


class AnnoyIndex(Index):

    def mk_index(self, items):
        logging.info("Start building annoy index")
        self.idx = annoy.AnnoyIndex(self.params.indexlength, metric="euclidean")
        if self.params.fixspeed:
            for n, item in enumerate(items):
                item = np.array(item)
                items[n] = list(128 * item / np.mean(item))
        for n, item in enumerate(items):
            self.idx.add_item(n, item)
        self.idx.build(20)

    def idx_get_length(self):
        return self.idx.get_n_items()

    def idx_get_nn(self, rownum, radius):
        result = []
        count = 20
        elem_idx, elem_dists = self.idx.get_nns_by_item(rownum,
                                                        count,
                                                        include_distances=True)
        for n, item in enumerate(elem_idx):
            if elem_dists[n] < radius:
                result.append(item)
        return result

    def idx_get_row(self, rownum):
        return self.idx.get_item_vector(rownum)
