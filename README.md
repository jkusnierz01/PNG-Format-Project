# E-Media Project 1: Analysis of Selected Multimedia File Format

## Project Overview

Created project focus on analysis of PNG image format, it enables user to:
 - inspect image critical chunks data (IHDR, IDAT, IEND)),
 - inspect image ancillary chunks data (eXIF, PLTE, gAMA, cHRM),
 - encrypt/decrypt image with ECB algorithm with use of RSA key-pairs,
 - encrypt/decrypt image with CBC algorithm with use of RSA key-pairs

## How to run?
First of all install requried librarys with poetry:
```
poetry install
```
and create environment:
```
poetry install
```


Then to run code simply type:
```
python3 main.py <path_to_image> [-flags]
```

Where the flags are:
```
-d', --displayImageData : Display Image Data stored in chunks
-r, --removeAnc : Remove all Ancillary Chunks from file
-e, --ecbencrypt : Encrypt image using ECB encryption method
-c, --cbcencrypt : Encrypt image using CBC encryption method
```


