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

Search database for possible duplicates and logs results as `ffplay`
commands

        viddup --db database --search 
        
E.g.:

        INFO:root:Group of 2 files found
        INFO:root:ffplay -ss 00:02:18 'Carinis-Classic-Cars-DMAX2018-02-1305-45.mkv'
        INFO:root:ffplay -ss 00:22:18 'Carinis-Classic-Cars-DMAX2018-02-1305-25.mkv'

You can launch a very basic UI with

        viddup --db database --search --ui
        
![viddup](https://user-images.githubusercontent.com/6553148/41529788-8b29d570-72ee-11e8-9329-e241780c0bca.png)
    

## Remove Obsolete Database Entries

List all filenames that need to be purged from the database:

        viddup --db database --purge
    
Really purge the database

        viddup --db database --purge --delete


Building
========

The binary Debian package will be built with
        
        git clone https://github.com/Eierkopp/viddup.git
        cd viddup
        dpkg-buildpackage -b

Installation
============

`viddup` itself is installed by

        dpkg -i viddup_1.0_all.deb

For the tool to work it needs one of the following k-nearest-neighbor
libraries

- [hnswlib](https://github.com/nmslib/hnsw)
- [cyflann](https://github.com/dougalsutherland/cyflann)
- [annoy](https://github.com/spotify/annoy)

`annoy` can be installed with 

        sudo pip3 install annoy
        
`cyflann` can be installed with
  
        sudo apt install libflann-dev
        sudo pip3 install cyflann
        
`hnswlib` can be installed with
    
        git clone https://github.com/nmslib/hnsw
        cd hnsw/python_bindings
        sudo python3 setup.py install

Details
=======

For each video the hash is just a sequence of time differences between
local maxima of brightness at the center of the frames. These are
computed with numpy's `argrelmax` mith order 10 * fps, i.e a local
maximum over in a range of 10 seconds.

The sequence of time differences is then cur into pieces of length
`indexlength`. When the timespan covered by such a piece exceeds
`scenelength`, the remaining values are replaced by 0.

In the last step a k-neares-neighbor library is used to find similar
sequences within the database.


    
