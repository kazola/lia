# Installation


## MSWindows

It is common for Windows python installations to not have ``pip`` installed.

Suggestion is going to python homepage, downloading a recent version but not the last one. For example, let's download v3.10.

[python3.10](https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe)

Then you select ``custom install`` and make sure ``pip`` is selected and install.

Also, make sure ``python`` and ``pip`` names are added to the PATH environment variable.

Once finished, you can see the versions of python you have installed with this command:

```console
C:\Users\admin>py -0
Installed Pythons found by py Launcher for Windows
 -3.10.11 *
 -3.7-64 
 -3.7-32
 -2.7-64
```

It is up to you to create a virtual environment to run the ``lia`` programs. 

To get the software, you might need to do something like this:

```console
    py -3.10.11 -m pip install git+https://github.com/kazola/lia.git --force-reinstall
```

## Linux / MacOS

Under Unix (it is up to you to create a virtual environment) you cando:

```console
    python3 -m pip install git+https://github.com/kazola/lia.git --force-reinstall
```

## Running

Now you should be able to run ``main_tdo``, ``main_dox`` and ``download`` examples by just typing them.

