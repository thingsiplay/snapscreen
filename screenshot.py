#!/bin/env python3

import sys
import time
import atexit
import os
import subprocess
import pathlib
import tempfile
import argparse
import configparser
# import shutil
import re

from typing import Union, Dict, List, Tuple

# Shorthands for types
Pathlib = pathlib.Path
Argparse = argparse.Namespace
GamelistEntry = Dict[str, Dict[str, Union[str, int, Pathlib]]]


# Parse all options and arguments of the program and get an argparse object.
def parse_arguments() -> Argparse:

    parser = argparse.ArgumentParser(
            description='Create automated screenshots with RetroArch using'
                        ' entryslots.'
    )

    parser.add_argument(
            '--gamelist',
            metavar='"gamelist.ini"',
            default='gamelist.ini',
            help='path to list of game profile setting',
    )

    parser.add_argument(
            '--shaderlist',
            metavar='"shaderlist.txt"',
            default='shaderlist.txt',
            help='path to text file with list of file paths of shaders',
    )

    parser.add_argument(
            '--shaderdir',
            metavar='"~/.config/retroarch/shaders/shaders_slang/"',
            default='~/.config/retroarch/shaders/shaders_slang/',
            help='path to RetroArch shaders folder to determine relative path'
    )

    parser.add_argument(
            '--appendconfig',
            metavar='"append.cfg"',
            default=[],
            action='append',
            help='path to retroarch config file to append temporarily, can be '
                 'used multiple times, each following file has higher '
                 'priority than the file specified before in the commandline '
                 'list',
    )

    parser.add_argument(
            '--config',
            metavar='"~/.config/retroarch/retroarch.cfg"',
            default='~/.config/retroarch/retroarch.cfg',
            help='path to base retroarch config file to read from',
    )

    parser.add_argument(
            '--outputdir',
            metavar='"screenshots/"',
            default='screenshots/',
            help='output folder for created screenshots',
    )

    parser.add_argument(
            '--statesdir',
            metavar='"states/"',
            default='states/',
            help='folder to look save states files in',
    )

    parser.add_argument(
            '--slot',
            metavar='1',
            default='1',
            type=int,
            help='number of entryslot from save state to load',
    )

    parser.add_argument(
            '--frames',
            metavar='5',
            default='5',
            type=int,
            help='number of frames to process before screen capture',
    )

    parser.add_argument(
            '--window',
            metavar='width+height',
            default=None,
            help='force window mode and set resolution, example: "1920+1080"',
    )

    parser.add_argument(
            '--sep',
            metavar='"／"',
            default='／',
            help='separator for screenshot filenames including subdirectories',
    )

    parser.add_argument(
            '--tries',
            metavar='5',
            default='5',
            type=int,
            help='number of times to run retroarch command until success',
    )

    parser.add_argument(
            '--force',
            action='store_true',
            help='force creating and overwrite existing files',
    )

    parser.add_argument(
            '--verbose',
            action='store_true',
            help='print additional information whats going on',
    )

    parser.add_argument(
            '--quiet',
            action='store_true',
            help='do not print anything to stdout',
    )

    args = parser.parse_args()

    return args


# Expand and resolve all parts of the file path string and make it a fullpath
# in pathlib format.
def path(
        file: str) -> Pathlib:

    expandedfile = os.path.expandvars(file)
    path = pathlib.Path(expandedfile).expanduser().resolve()

    return path


# Create the temporary file and register it to automatically deleted when
# entire script ends, even on crash.  The content will be filled up by the
# configuration files.
def create_tempconfig(
        settings) -> Pathlib:

    namedtempfile = tempfile.NamedTemporaryFile(
            prefix='tempconfig-',
            suffix='.cfg',
            delete=False,
    )
    tempconfig = pathlib.Path(namedtempfile.name)
    atexit.register(tempconfig.unlink, missing_ok=True)

    return tempconfig


# These settings are intended to be included on top of the config file,
# regardless of any settings or other user configuration files.  This is mainly
# to ensure not to overwrite main RetroArch configuration settings on exit and
# avoid user error.
def build_forceconfig() -> list[str]:

    config: list[str] = []
    config.append('config_save_on_exit = "false"')

    return config


def build_statesdirconfig(statesdir: Pathlib) -> list[str]:

    config: list[str] = []

    path = statesdir.expanduser().resolve()
    if path.exists():
        config.append('savestate_directory = "' + path.as_posix() + '"')

    print("path: ", path.as_posix())

    return config


def build_windowconfig(window_size) -> List[str]:

    config: List[str] = []
    (width, height) = (None, None)

    if window_size:
        if window_size == "720p":
            (width, height) = ("1280", "720")
        elif window_size == "1080p":
            (width, height) = ("1920", "1080")
        elif (window_size == "1440p"):
            (width, height) = ("2560", "1440")
        elif (window_size == "2160p" or window_size == "4k"):
            (width, height) = ("3840", "2160")
        else:
            match = re.search(r"(\d+)[+x](\d+)", window_size)
            if match:
                (width, height) = match.group(1, 2)
            else:
                raise ValueError('Try "1920+1080" format on option --window: '
                                 + str(window_size))

        config.append('video_fullscreen = "false"')
        config.append('video_windowed_fullscreen = "false"')
        config.append('video_window_show_decorations = "false"')
        config.append('video_window_custom_size_enable = "false"')
        config.append(f'video_window_auto_width_max = "{width}"')
        config.append(f'video_window_auto_height_max = "{height}"')
        config.append(f'video_windowed_position_width = "{width}"')
        config.append(f'video_windowed_position_height = "{height}"')

    return config


# Fill the temporary file with retroarch.cfg and all append.cfg config files.
# The order of appendfiles is important, because the first one has highest
# priority, as the options appear on top in the file.  RetroArch only reads the
# first found option and ignores anything after.
#
# tempfile: final output file to be used when making screenshots
# basefile: original retroarch.cfg
# appendfiles: list of append.cfg files with higher priority settings
# forceconfig: list of strings with the highest priority settings
def fill_tempconfig_content(
        tempfile: Pathlib,
        basefile: Pathlib,
        appendfiles: List[Pathlib],
        windowsize: str,
        statesdir: Pathlib):

    forceconfig: List[str] = build_forceconfig()
    windowconfig: List[str] = build_windowconfig(windowsize)
    statesdirconfig: List[str] = build_statesdirconfig(statesdir)
    with open(tempfile, 'w') as outfile:
        for line in forceconfig:
            outfile.write(line + '\n')
        for line in statesdirconfig:
            outfile.write(line + '\n')
        for line in windowconfig:
            outfile.write(line + '\n')
        for file in appendfiles:
            for line in open(file, 'r'):
                outfile.write(line)
        for line in open(basefile, 'r'):
            outfile.write(line)

    return 0


# Read shaderlist file and get a list of paths for each line.
def shaders_from_shaderlist(
        file: Pathlib) -> List[Pathlib]:
    lines: List[Pathlib] = []
    with open(file.as_posix()) as f:
        lines = [path(line.rstrip('\n')) for line in f]
    for shader in lines:
        if not shader.exists():
            raise FileNotFoundError(shader.as_posix())

    return lines


# Read gamelist in INI format and get a dictionary from all game sections and
# their keys.  Also converts each key to correct type and does basic validation
# of all keys.
# Note: Not all keys are used by this program, such as "size" and "pos".  These
# are just ignored, but maybe used by other applications.
def games_from_gamelist(
        file: Pathlib, args: Argparse) -> GamelistEntry:

    config = configparser.ConfigParser()
    config.read(file.as_posix())
    games: GamelistEntry = {}
    games = {title: dict(config.items(title)) for title in config.sections()}

    for title in games:
        game = path(config.get(title, 'game'))
        core = path(config.get(title, 'core'))
        slot = config.getint(title, 'slot', fallback=args.slot)
        frames = config.getint(title, 'frames', fallback=args.frames)
        sep = config.get(title, 'sep', fallback=args.sep)

        if not game.exists():
            raise FileNotFoundError(game.as_posix())
        if not core.exists():
            raise FileNotFoundError(core.as_posix())
        if slot not in range(1, 10):
            raise ValueError(f'[{title}] slot accepts only 1-9: '
                             + str(slot))
        if frames not in range(0, 1000):
            raise ValueError(f'[{title}] frames accepts only 0-999: '
                             + str(frames))
        if not len(sep) == 1:
            raise ValueError(f'[{title}] sep accepts only 1 character: {sep}')

        games[title]['game'] = game
        games[title]['core'] = core
        games[title]['slot'] = slot
        games[title]['frames'] = frames
        games[title]['sep'] = sep

    return games


# Create a dictionary of main settings for usage in the program.  The values
# can have any type, so due to the complexity no type checking is done.
def build_app_settings():

    args = parse_arguments()
    settings = {}
    settings['config'] = path(args.config)
    if args.appendconfig:
        settings['appendconfig'] = reversed([path(file) for
                                             file in args.appendconfig])
    else:
        settings['appendconfig'] = ['append.cfg']
    settings['gamelist'] = path(args.gamelist)
    settings['games'] = games_from_gamelist(settings['gamelist'], args)
    settings['shaderlist'] = path(args.shaderlist)
    settings['shaders'] = shaders_from_shaderlist(settings['shaderlist'])
    settings['shaderdir'] = path(args.shaderdir)
    settings['outputdir'] = path(args.outputdir)
    settings['statesdir'] = path(args.statesdir)
    settings['window'] = args.window
    settings['tries'] = args.tries
    settings['force'] = args.force
    settings['verbose'] = args.verbose
    settings['quiet'] = args.quiet
    settings['tempconfig'] = create_tempconfig(settings)

    return settings


# Build up the base command for RetroArch and whats the identical for all
# following game related commands.  As this includes the retroarch executable
# itself, this command needs to be merged at the beginning of main command.
def build_base_command(
        tempconfig: Pathlib) -> List[str]:

    command: List[str] = []
    command.append('retroarch')
    command.append('--config')
    command.append(tempconfig.as_posix())
    command.append('--sram-mode')
    command.append('noload-nosave')
    command.append('--max-frames-ss')
    command.append('--eof-exit')

    return command


# Build up the part of the command responsible for the game specific settings
# from the gamelist.ini file.  As this includes the path to the game ROM
# itself, this command needs to be merged at the end of main command.
def build_game_command(
        game: Dict[str, Union[str, int, Pathlib]]) -> List[str]:

    command: List[str] = []
    command.append('--max-frames')
    command.append(str(game['frames']))
    command.append('--entryslot')
    command.append(str(game['slot']))
    command.append('--libretro')
    command.append(str(game['core']))
    command.append(str(game['game']))

    return command


# Build up the command and file path to the new screenshot to create.
def build_screenshot_command(
        shaderfile, title, settings) -> Tuple[List[str], Pathlib]:

    path = build_screenshot_path(shaderfile,
                                 settings['shaderdir'],
                                 settings['outputdir'],
                                 title,
                                 settings['games'][title]['sep'])
    command: List[str] = []
    command.append('--max-frames-ss-path')
    command.append(path.as_posix())

    return command, path


# Format and name the file path to be used as the screenshot to save.
def build_screenshot_path(
        shaderfile: Pathlib, shaderdir: Pathlib, outputdir: Pathlib,
        title: str, sep: str) -> Pathlib:

    relative = shaderfile.relative_to(shaderdir)
    renamed = relative.with_suffix('.png').as_posix().replace('/', sep)
    path = pathlib.Path(
            outputdir.as_posix()
            + '/' + title
            + '/' + renamed
    )
    path.parent.mkdir(parents=True, exist_ok=True)

    return path


# The fun stuff.
def main() -> int:

    settings = build_app_settings()
    fill_tempconfig_content(settings['tempconfig'],
                            settings['config'],
                            settings['appendconfig'],
                            settings['window'],
                            settings['statesdir'])
    base_command = build_base_command(settings['tempconfig'])

    created_screenshots = 0
    for title in settings['games']:
        if not settings['quiet']:
            if settings['verbose']:
                print()
            print('Processing [' + title + '] ...')
        game_command = build_game_command(settings['games'][title])

        for shaderfile in settings['shaders']:
            screenshot_command, screenshot_file = build_screenshot_command(
                    shaderfile, title, settings)
            command: List[str] = []
            command.extend(base_command)
            command.append('--set-shader')
            command.append(shaderfile.as_posix())
            command.extend(screenshot_command)
            command.extend(game_command)
            if not settings['quiet'] and settings['verbose']:
                print()
                print(command)

            for _ in range(settings['tries']):
                if not settings['force'] and screenshot_file.exists():
                    break
                time.sleep(0.2)
                subprocess.run(command)
                time.sleep(0.2)
                if screenshot_file.exists():
                    created_screenshots += 1
                    break

    if not settings['quiet']:
        print()
        print(str(created_screenshots) + " screenshot(s) created.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
