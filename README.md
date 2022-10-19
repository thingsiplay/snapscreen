# snapscreen for RetroArch

Automate screenshot taking of RetroArch games on Linux

- Author: Tuncay D.
- Source: https://github.com/thingsiplay/snapscreen
- Update Notes: [CHANGES](CHANGES.md)
- License: [MIT License](LICENSE)

## What is this program?

**snapscreen** is a set of scripts and programs to automate the process of
running RetroArch to capture a screenshot on exit. This allows for
systematically creation of screenshots and crop collages in various
resolutions, various shaders and a list of games in a consistent manner. The
scripts are written in Python 3.10 and only tested with Linux.

It is important to read this document carefully. This is not a simple plug and
play solution and requires manual setup and an understanding of how it works.
The project started off as simple shell scripts and evolved over time to this
suite for my personal needs. I still hope others could find it useful.

## Quick Start

0. Install and setup
   [RetroArch](https://www.retroarch.com/index.php?page=linux-instructions) on
   Linux natively (no Flatpak or Steam version). Your distribution most likely
   have it in the repository. Example install command: `pamac install
   retroarch`
0. Install [ImageMagick](https://imagemagick.org/script/download.php) suite.
   Your distribution most likely have it in the repository. Example install
   command: `pamac install imagemagick`
0. Download [snapscreen for
   RetroArch](https://github.com/thingsiplay/snapscreen). Example download
   command: `git clone https://github.com/thingsiplay/snapscreen`
0. Make the scripts executable: `chmod +x *.py`
0. Copy and overwrite example files to main folder: `cp -rf examples/smw/* .`
   Choose `y` to overwrite the files.
0. Edit `gamelist.ini` and `shaderlist.txt` paths to adjust to your system. If
   you change the filename of the ROM, then adjust the filename of the
   savestate found in folder "states" too. Check if you have the core
   installed.
0. Run command to build screenshots: `./batch.py --resolution 720p,4k`
0. Sit back, enjoy and have fun.

## How to use

The usage itself is not hard. At the moment the scripts expect the
working/current directory to be where the "screenshot.py" and "crop.py" files
are. If you installed and configured everything, then just run the executables.
"batch.py" just automates the other two main scripts. At default it will create
4 different resolutions for each game/shader combo. In general, lookup the
internal `--help` options to see what you can set from commandline. A simple
command could look like these examples:

    $ ./screenshot.py --help

    $ ./crop.py --nocollage --force --verbose

    $ ./batch.py --resolution 1080p,4k

Note: Don't forget to make the scripts executable.

If you do not specify the option `--window` with width and hight for
"screenshot.py", then your monitors current resolution will be used. And it
will be in fullscreen; constantly switching on and off to fullscreen and
desktop. You can avoid this by specifying a window size. This cannot be a list.
Here are some examples:

    $ ./screenshot.py --window "1920+1080"

    $ ./screenshot.py --window "4k"

There are a few special names that you can use: "720p", "1080p", "1440p" and
"4k". And for the script "batch.py" there is no `--window` option, but a
`--resolution` option that works similar. Except it can be a comma separated
list. It defaults to all 4 known resolutions listed above. Here some examples:

    $ ./batch.py --resolution 720p

    $ ./batch.py --resolution "1920+1080,1440p"

## How to install?

There is no installation process for the **snapscreen**. Just download the
archive and extract it or `git clone
https://github.com/thingsiplay/snapscreen`. Make the ".py" files executable
with command `chmod +x *.py`.

You still need `retroarch` installed and setup, so that the script
"screenshot.py" can run it. A working environment of RetroArch is required.
Only the native installation of RetroArch on Linux is tested. To run the script
"crop.py", you need the ImageMagick suite, so it can convert using command
`convert` and create collages using command `montage`. Search in your
distributions repository for `imagemagick`, which should come with those
programs.

And I think that's it. Oh yes, and off course you need Python 3.10 or higher.
And a Linux operating system, because this is written for Linux and I have no
clue how or if it operates on Windows.

## How does it work?

TL;DR: "screenshot.py" takes each Shader from "shaderlist.txt" and runs
RetroArch on every game from "gamelist.ini" with the associated savestate file.
The file "append.cfg" contains additional settings for RetroArch. "crop.py"
will create crops and collages from the screenshots. "batch.py" is automating
both scripts.

### screenshot.py

It uses savestates at it's heart to load the game at the right moment. Then
commandline options are set to exit RetroArch after specific amount of frames
and combines it with the option to automatically save a screenshot at the end.
And to determine the correct settings for each game, a file named
"gamelist.ini" will be loaded up. It should contain the path of the ROM and
RetroArch core, plus optionally some additional settings. And similarly the
file "shaderdir.txt" contains a simple list of Shader file paths, that is used
for each game.

Also a very important part of the **snapscreen** suite is the "append.cfg"
configuration file for RetroArch. First "screenshot.py" will create a temporary
copy of the your personal retroarch.cfg settings file, so it does not get
manipulated by accident.  Also it makes sure that an option
`config_save_on_exit` is set to `"false"`, which additionally will prevent
accidentally editing your main configuration.  And then the "append.cfg" will
be automatically added to the temporary copy of your main configuration file.
It contains settings that help with the screenshot process, such as temporarily
disabling audio and notifications in example. It also uses a different
temporary folder for save files, so your personal progress does not get
overwritten when loading a savestate file.

This is all done by the main script "screenshot.py". At default every
screenshot configuration is loaded separately in a fullscreen. But the script
allows for windowed mode too. Because of the approach with savestate files, the
creation of screenshots is limited to cores which support savestates. And BTW
it will only generate non existent screenshots. So if you add a new game
configuration, resolution or shader to your list, then only the new stuff is
generated.

### crop.py

In the next step the script "crop.py" can be used to create 100% view crops of
each screenshot and single collage images containing all crops. It will read
the same "gamelist.ini" file to determine which portion (position and size) of
the screenshots for each game setup should be cropped. If you have any
resolution dependent settings, then you need to create an entire copy
"gamelist.ini" file with the specific changes.

To have "crop.py" working, some programs are needed on your system. It uses the
ImageMagick commands `convert` and `montage` to create the files. So the
package `imagemagick` should be installed before using "crop.py".

### batch.py

This is an automation for automation. "batch.py" is simply running
"screenshot.py" and then "crop.py" in a loop of multiple resolution settings.
There is not much else to say. Other than maybe that the default resolution
includes the 4 major "720p,1080p,1440p,4k" and does not default to your
monitors current resolution, as "screenshot.py" would.

## How to configure

There are multiple files to setup. The "append.cfg" is preconfigured and should
be enough for the RetroArch settings. So your job is 1) creating the
savestates, 2) setting up "gamelist.ini" and 3) list all Shaders in
"shaderlist.txt".

Note: There are example projects in the "examples/" folder. Each subdirectory
contains additional files to copy into the main directory of **snapscreen**.
Mainly consisting of "gamelist.ini", "shaderlist.txt" and the savestates in
"states" folder. Just override the existing files.

### Save States

First, you need to play a game to the point you want to make a screenshot from.
Then, go into RetroArch savestate folder "states" and go into the cores folder.
I don't know how you setup your RetroArch configuration and folder structure,
but once you found the savestate file with extension ".stateX" ("X" is a number
here), copy the file, then go to your **snapscreen** "states" directory and
create the same folder for the core you got the savestate file from. In example
"Mesen-S". Now put the savestate file into the folder for the core. Example:

From:

    ~/.config/retroarch/states/Mesen-S/Super Mario World (U) [!].state1

To:

    ~/Downloads/snapscreen/states/Mesen-S/Super Mario World (U) [!].state1

Next, rename the extension ".stateX" file to ".state1", if it is a different
number. This is not necessary, but it makes it easier to work with. Because
this number defines what "slot" index it is. Details not important now, just so
you know this is the option `--slot` on commandline or `slot=` option found in
"gamelist.ini", which defaults to "1" for ".state1.entry". After this, you
*need* to add the extension ".entry" to the filename. It should look like this:

    ~/Downloads/snapscreen/states/Mesen-S/Super Mario World (U) [!].state1.entry

Now the savestate is ready to be loaded.

### gamelist.ini

Now comes the hard part. This file contains all paths and settings needed to
take a screenshot. It is a typical config file similar to Windows INI format.
The `[Super Mario World]` section header is a custom name chosen by you, to
represent the game as a folder and later in collage titles. Then each entry
needs a `game=` key, pointing to the game ROM file. Similarly you need a `core`
key entry pointing to the emulator core. Here is an example how it would look
like on my Linux machine:

    [Super Mario World]
    game=~/Emulatoren/games/snes/Super Mario World (U) [!].smc
    core=~/.config/retroarch/cores/mesen-s_libretro.so

The name of the ROM should match the name of the ".state1.entry" file, so it
can be found. The file extensions are not compared here, just the basename of
the files. Usually that is the case when saving savestates with RetroArch. So
following is a match:

    Super Mario World (U) [!].state1.entry
    Super Mario World (U) [!].smc

It can contain as many game entries as you like. There is also a default
section named `[DEFAULT]`. Any missing setting in the game entry will lookup
this default section for default settings. There is no need for this section,
because the scripts itself have default values anyway. But you can change the
default values with it.

An option named `pos=` can be added to specify at which position a crop should
be done. This is only relevant to the script "crop.py". Here is an example for
setting the starting point of a crop at x and y values to "64":

    [DEFAULT]
    frames=5

    [Super Mario World]
    game=~/Emulatoren/games/snes/Super Mario World (U) [!].smc
    core=~/.config/retroarch/cores/mesen-s_libretro.so
    pos=64+64

BTW the option `frames=` mean how many frames it should past before taking a
screenshot.

### shaderlist.txt

Simply list all Shader file paths you want make screenshots with. Each Shader
file should be listed separated by newline character. At the moment this only
works with files saved in your `--shaderdir` directory variable. At default
this points to `"~/.config/retroarch/shaders/shaders_slang/"`. An example list:

    ~/.config/retroarch/shaders/shaders_slang/nearest.slangp
    ~/.config/retroarch/shaders/shaders_slang/presets/scalefx+rAA+aa.slangp

Every game you setup in "gamelist.ini" will be run with each Shader from this
list.

