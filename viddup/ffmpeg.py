#!python3
# coding: utf-8

import json
import logging
import numpy as np
import shlex
import subprocess

CROP_FLT = "crop=in_w/10:in_h/10:in_w*0.45:in_h*0.45"
OUT_FMT = "-f image2pipe -pix_fmt rgb24 -vcodec rawvideo"
OPT_FLAGS = ""  # "-hwaccel vaapi"


class HashStream:

    def __init__(self, vidname):
        self.vidname = vidname
        self.framebytes = self.fetch_frame_bytes()
        self.fps, self.duration = self.fetch_fps_duration()
        self.nframes = int(self.fps * self.duration)

    def fetch_frame_bytes(self):
        data = subprocess.check_output(
            shlex.split(
                f"ffmpeg -v 0 -i {self.vidname} -an -vf '{CROP_FLT}' {OUT_FMT} -vframes 1 pipe:"
            )
        )
        return len(data)

    def fetch_fps_duration(self):

        data = subprocess.check_output(
            shlex.split(
                f"ffprobe -v 0 -of json -select_streams v:0 -show_entries format:stream {self.vidname}"
            ),
            encoding="utf-8",
        )
        details = json.loads(data)
        fps = details["streams"][0]["r_frame_rate"]
        if "/" in fps:
            num, denom = fps.split("/")
            fps = float(num) / float(denom)
        else:
            fps = float(fps)
        duration = float(details["format"]["duration"])
        return fps, duration

    def read_hashes(self):
        cmd = shlex.split(
            f"ffmpeg {OPT_FLAGS} -i {self.vidname} -an -vf '{CROP_FLT}' {OUT_FMT} pipe:"
        )
        try:
            with subprocess.Popen(
                cmd, stdin=None, stderr=subprocess.DEVNULL, stdout=subprocess.PIPE
            ) as proc:
                while buf := proc.stdout.read(self.framebytes):
                    yield np.mean(np.frombuffer(buf, dtype=np.uint8))
        except Exception as e:
            logging.info("Exception during read: %s", e, exc_info=True)
