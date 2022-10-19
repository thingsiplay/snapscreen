#!/bin/env python3


import sys
import os
import pathlib
import subprocess
import argparse


def parse_arguments() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
            description='Create automated crops from RetroArch screenshots'
    )

    parser.add_argument(
            '--screenshot',
            metavar='"screenshot.py"',
            default='screenshot.py',
            help='path to the screenshot script utility',
    )

    parser.add_argument(
            '--crop',
            metavar='"crop.py"',
            default='crop.py',
            help='path to the crop script utility',
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
            '--resolution',
            metavar='"720p,1080p,1440p,4k"',
            default='720p,1080p,1440p,4k',
            help='comma separated list of sizes, example:"1920+1080,4k"',
    )

    parser.add_argument(
            '--webp',
            action='store_true',
            help='convert collages to lossless .webp format, keep the .png',
    )

    args = parser.parse_args()

    return args


def path(
        file: str) -> pathlib.Path:

    expandedfile = os.path.expandvars(file)
    path = pathlib.Path(expandedfile).expanduser().resolve()

    return path


def main() -> int:

    args = parse_arguments()

    screenshot_script = path(args.screenshot)
    crop_script = path(args.crop)
    if args.appendconfig:
        appendconfig = [path(file) for file in args.appendconfig]
    else:
        appendconfig = [pathlib.Path('append.cfg')]

    for resolution in args.resolution.split(','):

        screenshots_dir = path('./screenshots').joinpath(resolution)
        crops_dir = path('./crops').joinpath(resolution)

        s_command = []
        s_command.append(screenshot_script.as_posix())
        for file in appendconfig:
            s_command.append('--appendconfig')
            s_command.append(file.as_posix())
        s_command.append('--window')
        s_command.append(resolution)
        s_command.append('--gamelist')
        s_command.append(args.gamelist)
        s_command.append('--shaderlist')
        s_command.append(args.shaderlist)
        s_command.append('--outputdir')
        s_command.append(screenshots_dir.as_posix())

        c_command = []
        c_command.append(crop_script.as_posix())
        if args.webp:
            c_command.append('--webp')
        c_command.append('--gamelist')
        c_command.append(args.gamelist)
        c_command.append('--inputdir')
        c_command.append(screenshots_dir.as_posix())
        c_command.append('--outputdir')
        c_command.append(crops_dir.as_posix())

        screenshots_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(s_command)

        crops_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(c_command)

    return 0


if __name__ == '__main__':
    sys.exit(main())
