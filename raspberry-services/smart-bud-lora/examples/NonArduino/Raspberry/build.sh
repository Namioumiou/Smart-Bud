#!/bin/bash

set -e
mkdir -p build
cd build
cmake -G "CodeBlocks - Unix Makefiles" ..
make
cd ..
size build/rpi-sx1262
mv -f ./build/rpi-sx1262 /usr/local/bin/rpi-sx1262
rm -drf build 
