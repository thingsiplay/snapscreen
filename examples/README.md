# Examples for snapscreen

These folders are example projects that can be used with
https://github.com/thingsiplay/snapscreen . Just copy the content of the
subfolder into the main directory of **snapscreen** folder and override
existing files. In example with the command:

    $ cp -rf examples/smw/* .

However, compatibility with savestates cannot be guaranteed. They might not
work in the future. These are just examples how to setup a project. Some
projects are just replacing the default "gamelist.ini" and "shaderlist.txt"
files. Those can be run with the default script parameters. Some projects may
require additional parameters and arguments to set in commandline. An example
are the multiple resolution variants of sonkun's Shader presets. First copy the
files:

    $ cp -rf examples/sonkun/* .

And here is an example how to run each resolution on their own:

    $ ./batch.py --resolution 1080p --gamelist gamelist_1080p.ini --shaderlist shaderlist_1080p.txt

Also obviously don't forget to edit the settings and paths in the
"gamelist.ini" and "shaderlist.txt" files.
