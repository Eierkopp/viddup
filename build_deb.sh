#!/bin/bash

cd "$(dirname $0)" || exit

export MYPYPATH=lib
mypy bin/viddup

dpkg-parsechangelog
echo "-----------------------------------------"
echo "press enter to continue"
read -r
dpkg-buildpackage -b --no-sign

dpkg-deb -c "../viddup_$(dpkg-parsechangelog -S version)_amd64.deb"
