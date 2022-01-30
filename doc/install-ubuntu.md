Installing FlatCAM on Ubuntu

So FlatCAM is an essential part of my PCB milling workflow and has become increasingly difficult to install on the latest version of Ubuntu. Here’s a couple of notes on how I managed to get it running.

The first thing is to clone the repo:

```shell
git clone https://bitbucket.org/jpcgt/flatcam
```

Something I didn’t notice at first is that there’s a beta branch available, it uses newer versions of pyqt which makes everything way easier.

```shell
git checkout origin/Beta
```

If you are on Ubuntu you can run ubuntu_setup.sh and should install pretty much everything you need. I did hit a snag though, for whatever reason if I tried installing the requirements, gdal would not compile. Turns out it comes down to it not finding the correct headers. You can get around it by installing it manually like this:

```shell
sudo apt install libgdal-dev gdal-bin
pip install gdal==3.0.4 --global-option=build_ext --global-option="-I/usr/include/gdal/"
```

You should use whatever version `gdal-config --version` prints out. You should also update the requirements.txt so that the version of gdal is also the same so that the rest of the dependencies install.

Once that’s up you can run it with `python FlatCAM.py`.

Reference: https://martianwabbit.com/2021/01/22/installing-flatcam-with-pyenv.html
