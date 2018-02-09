#!/usr/bin/env python3

"""
Copyright 2018 Jocelyn Falempe kdj0c@djinvi.net

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


from onepagebatch import generateFaction
import os
import argparse


def main():
    default_factions = ['Battle_Brothers', 'High_Elf_Fleets', 'Robot_Legions', 'Tao', 'Orc']

    parser = argparse.ArgumentParser(description='This script will compute the Unit costs and upgrade costs for a faction, and write html output')
    parser.add_argument('factions', type=str, nargs='*', default=default_factions,
                        help='path to the faction (should contain at list equipments.yml, units.yml, upgrades.yml)')

    args = parser.parse_args()

    for faction in args.factions:
        generateFaction(faction)


if __name__ == "__main__":
    # execute only if run as a script
    main()
