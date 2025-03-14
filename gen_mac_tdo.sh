#!/usr/bin/env bash


clear

pyinstaller --onefile main_tdo.py  \
    --add-data="data_files/$1:data_files" \
    --distpath _pyinstaller/dist \
    --workpath _pyinstaller/build \
    --icon=data_files/li.ico


rv=$?
if [ $rv -eq 0 ]; then
    echo
    echo 'copying executable as main_tdo_mac...'
    cp _pyinstaller/dist/main_tdo gen/main_tdo_mac
    echo 'done'
fi

mv ./*.spec _pyinstaller

