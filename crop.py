#!/bin/env python3

import sys
import os
import pathlib
import subprocess
import argparse
import configparser
import re

from typing import Union, Dict, List, Tuple

# Shorthands for types
Pathlib = pathlib.Path
Argparse = argparse.Namespace
GamelistEntry = Dict[str, Dict[str, Union[str, int, Pathlib]]]


def parse_arguments() -> Argparse:

    parser = argparse.ArgumentParser(
            description='Create automated crops from RetroArch screenshots'
    )

    parser.add_argument(
            '--gamelist',
            metavar='"gamelist.ini"',
            default='gamelist.ini',
            help='path to list of game profile setting',
    )

    parser.add_argument(
            '--inputdir',
            metavar='"screenshots/"',
            default='screenshots/',
            help='source folder of screenshots to create crops of',
    )

    parser.add_argument(
            '--outputdir',
            metavar='"crops/"',
            default='crops/',
            help='output folder for created crops',
    )

    parser.add_argument(
            '--sep',
            metavar='"／"',
            default='／',
            help='separator in screenshot filenames including subdirectories',
    )

    parser.add_argument(
            '--size',
            metavar='"480x480"',
            default='480x480',
            help='default height and width of the crop size',
    )

    parser.add_argument(
            '--pos',
            metavar='"0+0"',
            default='0+0',
            help='default region of the starting position',
    )

    parser.add_argument(
            '--force',
            action='store_true',
            help='force creating and overwrite existing files',
    )

    parser.add_argument(
            '--nocollage',
            action='store_true',
            help='will pass on creating collages out of the crops',
    )

    parser.add_argument(
            '--webp',
            action='store_true',
            help='convert collages to lossless .webp format, keep the .png',
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


# Read gamelist in INI format and get a dictionary from all game sections and
# their keys.  Also converts each key to correct type and does basic validation
# of all keys.
# Note: Not all keys are used by this program, such as "slot" and "frames".
# These are just ignored, but maybe used by other applications.
def games_from_gamelist(
        file: Pathlib, args: Argparse) -> GamelistEntry:

    config = configparser.ConfigParser()
    config.read(file.as_posix())
    games: GamelistEntry = {}
    games = {title: dict(config.items(title)) for title in config.sections()}

    size_format = re.compile(r'^[1-9]\d*x[1-9]\d*$')
    pos_format = re.compile(r'^\d+[+]\d+$')

    for title in games:
        game = path(config.get(title, 'game'))
        core = path(config.get(title, 'core'))
        sep = config.get(title, 'sep', fallback=args.sep)
        size = config.get(title, 'size', fallback=args.size)
        pos = config.get(title, 'pos', fallback=args.pos)

        if not game.exists():
            raise FileNotFoundError(game.as_posix())
        if not core.exists():
            raise FileNotFoundError(core.as_posix())
        if not len(sep) == 1:
            raise ValueError(f'{title} sep accepts only 1 character: {sep}')
        if not size_format.match(size):
            raise ValueError(f'{title} size has wrong format: {size}')
        if not pos_format.match(pos):
            raise ValueError(f'{title} pos has wrong format: {pos}')

        games[title]['game'] = game
        games[title]['core'] = core
        games[title]['sep'] = sep
        games[title]['size'] = size
        games[title]['pos'] = pos

    return games


# Reads in all screenshot files created previously for use as source to create
# the crops.
def collect_screenshot_files(
        inputdir: Pathlib, title: str) -> List[Pathlib]:

    gamedir = pathlib.Path(inputdir / title)
    files = [file for file in gamedir.iterdir() if file.is_file()]

    return files


def collect_files(
        inputdir: Pathlib, pattern: str = '*'):

    files = [f.as_posix() for f in inputdir.glob(pattern)]

    return files


# Reads all cropped files and create a sorted list, with the exeption of
# nearest and bilinear named files.  Those are always at start of list.
def collect_crop_files(
        inputdir: Pathlib) -> List[Pathlib]:

    first: List[Pathlib] = []
    second: List[Pathlib] = []
    files: List[Pathlib] = []
    for file in inputdir.iterdir():
        if not file.is_file() or not file.suffix == '.png':
            continue
        elif file.stem.startswith('nearest'):
            first.append(file)
        elif file.stem.startswith('bilinear'):
            second.append(file)
        else:
            files.append(file)
    files.sort()

    return first + second + files


# Create a dictionary of main settings for usage in the program.  The values
# can have any type, so due to the complexity no type checking is done.
def build_app_settings():

    args = parse_arguments()
    settings = {}
    settings['gamelist'] = path(args.gamelist)
    settings['games'] = games_from_gamelist(settings['gamelist'], args)
    settings['inputdir'] = path(args.inputdir)
    settings['outputdir'] = path(args.outputdir)
    settings['sep'] = args.sep
    settings['size'] = args.size
    settings['pos'] = args.pos
    settings['force'] = args.force
    settings['nocollage'] = args.nocollage
    settings['webp'] = args.webp
    settings['verbose'] = args.verbose
    settings['quiet'] = args.quiet

    return settings


# Combines both size and pos to geometry, which the convert command uses as a
# single option.
def build_geometry(
        games: dict, title: str) -> str:

    size = games[title]['size']
    pos = games[title]['pos']
    geometry = size + '+' + pos

    return geometry


# Builds up the convert command to crop a screenshot.  If the file already
# exists, then an empty list is returned.
def build_crop_command(
        settings: GamelistEntry, outgamedir: Pathlib, infile: Pathlib,
        geometry: str) -> Tuple[List[str], Pathlib]:

    command: List[str] = []
    outfile = pathlib.Path(outgamedir / infile.stem)
    outfile = outfile.with_stem(infile.stem + '-crop' + geometry + '.png')
    if not settings['force'] and outfile.exists():
        return command, outfile
    command.append('convert')
    command.append(infile.as_posix())
    command.append('-crop')
    command.append(geometry)
    command.append(outfile.as_posix())

    return command, outfile


# Base command for a game collage.  It will set the standard size for all
# images and their frame size.  It includes the main program to create the
# collage, so this should be the first command when merging with other command
# sets.
def build_collage_base_command(
        settings: dict, title: str, outfile: Pathlib) -> List[str]:

    command: List[str] = []
    if not settings['force'] and outfile.exists():
        return command
    command.append('montage')
    command.append('-frame')
    command.append('8x8')
    command.append('-geometry')
    command.append(settings['games'][title]['size'])
    command.append('-title')
    command.append(title)

    return command


# Base command to convert images into lossless webp format.
def build_towebp_base_command() -> List[str]:

    command: List[str] = []
    command.append('mogrify')
    command.append('-quality')
    command.append('100%')
    command.append('-format')
    command.append('webp')
    command.append('-define')
    command.append('webp:lossless=true')

    return command


# This will build the command set for a cropfile of a specific game.  It is
# intended to be run in a loop of game directory.
def build_collage_game_command(
        infile: Pathlib, sep: str) -> List[str]:

    label = infile.stem.partition('-crop')[0]
    command: List[str] = []
    command.append('-label')
    if label.startswith('nearest') or label.startswith('bilinear'):
        command.append(label)
    else:
        command.append(label.replace(sep, ' / '))
    command.append(infile.as_posix())

    return command


# The fun stuff.
def main() -> int:

    settings = build_app_settings()

    created_crops = 0
    created_collages = 0
    for title in settings['games']:
        if not settings['quiet']:
            if settings['verbose']:
                print()
            print('Processing [' + title + '] ...')
        geometry = build_geometry(settings['games'], title)
        outgamedir = pathlib.Path(settings['outputdir'] / title)
        outgamedir.mkdir(parents=True, exist_ok=True)
        screenshots = collect_screenshot_files(settings['inputdir'], title)
        sep = settings['games'][title]['sep']

        # Crop
        for infile in screenshots:
            crop_command, crop_file = build_crop_command(settings,
                                                         outgamedir,
                                                         infile,
                                                         geometry)
            if not crop_command:
                continue
            elif not settings['quiet'] and settings['verbose']:
                print(crop_command)
                print()
            subprocess.run(crop_command)
            if crop_file.exists():
                created_crops += 1

        # Collage
        if settings['nocollage']:
            continue
        collage_path = pathlib.Path(settings['outputdir'].as_posix()
                                    + '/'
                                    + title
                                    + '-crop-collage.png')
        base_command = build_collage_base_command(settings,
                                                  title,
                                                  collage_path)
        if not base_command:
            continue

        crops = collect_crop_files(outgamedir)
        game_command: List[str] = []
        for infile in crops:
            command = build_collage_game_command(infile, sep)
            game_command.extend(command)

        collage_command: List[str] = []
        collage_command.extend(base_command)
        collage_command.extend(game_command)
        collage_command.append(collage_path.as_posix())
        if not settings['quiet'] and settings['verbose']:
            print(collage_command)
            print()
        subprocess.run(collage_command)
        if collage_path.exists():
            created_collages += 1

    if settings['webp']:
        if not settings['quiet']:
            if settings['verbose']:
                print()
            print('Processing webp conversion for collages ...')
        towebp_command = build_towebp_base_command()
        pngfiles = collect_files(settings['outputdir'], '*.png')
        subprocess.run(towebp_command + pngfiles)

    if not settings['quiet']:
        print()
        print(str(created_crops) + " crop(s) created.")
        print(str(created_collages) + " collage(s) created.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
