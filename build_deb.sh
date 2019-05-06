#!/bin/bash

cd `dirname $0`

dpkg-buildpackage -b --no-sign
