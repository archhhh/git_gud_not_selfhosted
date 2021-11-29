# Git Gud

Single branch implementation of git from scratch. The data structures, CLI follows the same structure as in 
the original git implementation.

### Why?

The attempt to finally understand better what is going on under the hood of the tool of my constant use.
To discover the design choices that make git

### Stack

Python 3.8 with the help of native libs (hashlib for SHA1 hash algorithm, zlib for compression, pathlib to work with paths).
Used pytz to work with dates, pytest, pyfakefs for tests

## What is in the package 

- init
- commit with staging
- logging the commits
- checking out the commits
- unit/integration tests with moderate coverage

## What is not in the package

- multibranching and operations related to it
- remote repos
- diff and status report
- and basically everything that's not included in what's in the package

## Models (UML)
![Untitled Diagram](https://user-images.githubusercontent.com/26677794/143918700-85c94f17-f9da-4a9a-b243-64c929096dc9.png)
