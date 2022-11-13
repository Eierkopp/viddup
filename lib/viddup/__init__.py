import argparse
import importlib
import logging
import sys
from typing import List, Optional

from .postgresql_db import FileInfo
from .postgresql_db import DB
from .index import Index

__all__ = ["get_db", "FileInfo"]


def get_db(params: argparse.Namespace) -> DB:
    return DB(params)


installed_libs = None  # type: Optional[List[str]]


def installed_knn_libs() -> List[str]:

    global installed_libs

    if installed_libs is None:
        installed_libs = list()

        for module_name in ["hnswlib", "cyflann", "annoy"]:
            try:
                importlib.import_module(module_name)
                installed_libs.append(module_name)
            except ModuleNotFoundError:
                pass

        if not installed_libs:
            logging.warning("No knnlib installed, search will not work")

    return installed_libs


def get_index(dbi: DB, args: argparse.Namespace) -> Index:
    libs = installed_knn_libs()
    if not libs:
        logging.error("No knn library installed, giving up")
        sys.exit(1)

    if args.knnlib:
        if args.knnlib in libs:
            lib = args.knnlib
        else:
            lib = libs[0]
            logging.warning("knnlib %s not installed", args.knnlib)
    else:
        lib = libs[0]
    logging.info("using knnlib %s", lib)

    if lib == "annoy":
        from .annoy_index import AnnoyIndex
        return AnnoyIndex(dbi, args)
    if lib == "cyflann":
        from .cyflann_index import CyflannIndex
        return CyflannIndex(dbi, args)
    if lib == "hnswlib":
        from .hnswlib_index import HnswlibIndex
        return HnswlibIndex(dbi, args)

    raise ModuleNotFoundError()
