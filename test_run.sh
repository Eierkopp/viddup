#!/bin/bash

cd `dirname $0`

export PYTHONPATH=lib

bin/viddup --dbhost gateway --dbport 5432 --dbname viddup_test --dbuser viddup --dbpwd viddup --ignore_start 600 --ignore_end 600 --fixduration $*
