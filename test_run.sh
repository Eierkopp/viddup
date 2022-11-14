#!/bin/bash

cd `dirname $0`

export PYTHONPATH=lib

# python3 bin/viddup --dbhost gateway --dbport 5432 --dbname viddup --dbuser viddup --dbpwd viddup --fixrenames --dir /media/data/.Pron
python3 bin/viddup --dbhost gateway --dbport 5432 --dbname viddup --dbuser viddup --dbpwd viddup --knnlib annoy --search --ui
# python3 bin/viddup --dbhost gateway --dbport 5432 --dbname viddup --dbuser viddup --dbpwd viddup --fixrenames --dir /home/depp/downloads
