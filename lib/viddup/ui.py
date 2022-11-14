#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import gi
import gi.repository
import logging
import os
import subprocess
import time
from typing import List, Any

from .tools import format_duration, whitelist, handle_purge
from viddup import DB, FileInfo

gi.require_version('Gtk', '3.0')  # noqa: E402
from gi.repository import Gtk, GLib  # noqa: E402


class VidDupUI(object):

    def __init__(self, dbi: DB, params: argparse.Namespace, duplicates: List[List[List[Any]]]):
        self.dbi = dbi
        self.params = params
        self.duplicates = duplicates

    def start(self) -> None:
        self.builder = Gtk.Builder()
        self.builder.add_from_file("/usr/share/viddup/viddup.glade")

        window = self.builder.get_object("app")

        data_grid = Gtk.Grid()
        data_grid.insert_column(0)
        data_grid.insert_column(0)
        data_grid.insert_column(0)
        rows = 0
        for index, group in enumerate(self.duplicates):
            for row in group:
                fileinfo, offset = row
                fn = Gtk.Label(label=self.make_label(fileinfo), xalign=0, xpad=10)
                row.append(fn)
                offset = Gtk.Label(label=format_duration(offset), xalign=0, xpad=10)
                delete = Gtk.Button(label="delete")
                delete.connect("clicked", self.onDelete, fileinfo.name)
                data_grid.insert_row(rows)
                data_grid.attach(fn, 0, rows, 1, 1)
                data_grid.attach(offset, 1, rows, 1, 1)
                data_grid.attach(delete, 2, rows, 1, 1)
                rows += 1
            box = Gtk.Box(orientation="horizontal")
            play = Gtk.Button(label="play")
            play.connect("clicked", self.onPlay, index)
            box.pack_start(play, expand=False, fill=True, padding=0)
            whitelist = Gtk.Button(label="whitelist")
            whitelist.connect("clicked", self.onWhitelist, index)
            box.pack_start(whitelist, expand=False, fill=True, padding=0)
            box.pack_end(Gtk.Label(), expand=True, fill=True, padding=0)
            data_grid.insert_row(rows)
            data_grid.attach(box, 0, rows, 3, 1)
            rows += 1

        main_area = self.builder.get_object("main_area")
        main_area.add(data_grid)

        self.builder.connect_signals(self)

        window.show_all()

        Gtk.main()

    def onPlay(self, *args) -> None:
        index = args[1]
        procs = []
        for fileinfo, offset, _ in self.duplicates[index]:
            if os.access(fileinfo.name, os.R_OK):
                procs.append(subprocess.Popen(["ffplay", "-sn", "-ss",
                                               format_duration(offset),
                                               fileinfo.name],
                                              stdout=subprocess.DEVNULL,
                                              stderr=subprocess.DEVNULL))

        finished = not bool(procs)
        while not finished:
            for p in procs:
                if (0, 0) != os.waitpid(p.pid, os.WNOHANG):
                    finished = True
                    break
            time.sleep(0.2)

        for p in procs:
            try:
                p.kill()
            except Exception:
                pass

    def onWhitelist(self, *args) -> None:
        args[0].destroy()
        index = args[1]
        fnames = [d[0].name for d in self.duplicates[index]]
        whitelist(self.dbi, self.params, fnames)

    def onDelete(self, *args) -> None:
        fname = args[1]
        try:
            os.remove(fname)
            logging.info("Deleted %s", fname)
            for group in self.duplicates:
                for fileinfo, offset, label in group:
                    if fname == fileinfo.name:
                        label.set_markup("<span strikethrough='true'>%s</span>"
                                         % GLib.markup_escape_text(self.make_label(fileinfo)))
                        label.set_use_markup(True)
        except Exception as e:
            logging.error("Failed to delete %s: %s", fname, e)

    def onQuit(self, *args) -> None:
        Gtk.main_quit(*args)

    def onPurge(self, *args) -> None:
        switch = self.builder.get_object("delete_switch")
        handle_purge(self.dbi, self.params, switch.get_active())

    def make_label(self, fileinfo: FileInfo) -> str:
        return format_duration(fileinfo.duration) + " " + fileinfo.name
