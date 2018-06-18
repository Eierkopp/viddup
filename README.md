viddup
======

`viddup` is a small tool to detect duplicate video scenes

Usage
=====

There are three typical use-cases for viddup:

1. Import video hashes into a database
1. Search hashes for duplicates
1. Remove obsolete entries from the database
    
## Importing Hashes

Import all movies from a directory

        viddup --db database --dir directory
 
## Search Hash Database

Search database for possible duplicates and dump results as a `json`
structure

        viddup --db database --search 
    

## Remove Obsolete Database Entries

List all filenames that need to be purged from the database:

        viddup --db database --purge
    
Really purge the database

        viddup --db database --purge --delete
    

Installation
============

`viddup` needs one of the following k-nearest-neighbor libraries to
work. 

- [hnswlib](https://github.com/nmslib/hnsw)
- [cyflann](https://github.com/dougalsutherland/cyflann)
- [annoy](https://github.com/spotify/annoy)

