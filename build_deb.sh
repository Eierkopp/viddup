#!/bin/bash

cd `dirname $0`

dpkg-parsechangelog
echo "-----------------------------------------"
echo "press enter to continue"
read x
dpkg-buildpackage -b --no-sign
