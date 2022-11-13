#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging

import cyflann
import numpy as np

from .index import Index


class CyflannIndex(Index):

    def mk_index(self, items):
        logging.info("Start building flann index")
        self.idx = cyflann.FLANNIndex(algorithm="kdtree")
        if self.params.fixspeed:
            for n, item in enumerate(items):
                item = np.array(item)
                items[n] = list(128 * item / np.mean(item))
        self.idx.build_index(items)

    def idx_get_length(self):
        return len(self.idx.data)

    def idx_get_nn(self, rownum, radius):
        row = self.idx.data[rownum]
        elem_idx, _ = self.idx.nn_radius(row, radius, sorted=True)
        return elem_idx

    def idx_get_row(self, rownum):
        return self.idx.data[rownum]
