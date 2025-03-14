#!/usr/bin/env bash


clear

pyinstaller --onefile main_dox.py  \
    --distpath _pyinstaller/dist \
    --workpath _pyinstaller/build \
    --icon=data_files/li.ico
    # --add-data="data_files/$1:data_files" \



rv=$?
if [ $rv -eq 0 ]; then
    echo
    echo 'copying executable as main_dox_linux...'
    cp _pyinstaller/dist/main_dox gen/main_dox_linux
    echo 'done'
fi

mv ./*.spec _pyinstaller

