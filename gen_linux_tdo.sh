#!/usr/bin/env bash

 pyinstaller --onefile main_tdo --distpath _pyinstaller/dist --workpath _pyinstaller/build
pyinstaller --onefile main_tst.py  --distpath _pyinstaller/dist --workpath _pyinstaller/build --add-data="data_files/my_file.txt:data_files"