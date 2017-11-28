#!/bin/bash

for f in `find . -name "*.yml" -o -name "*.tex"` ; do
  echo "Processing ${f}"
  mv "${f}" "${f}_"
  iconv -f utf8 -t ascii//TRANSLIT "${f}_" -o "${f}"
  rm "${f}_"
done
