#!/usr/bin/env python3

"""
Copyright 2017 Jocelyn Falempe kdj0c@djinvi.net

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

from pyexcel_ods3 import get_data, save_data
import json
import argparse
import string
from collections import OrderedDict

"""
This scripts helps to generate the json files for a faction.
It takes a libreoffice calc ".ods" file, and generate the list
of weapons, and units.
The libreoffice calc file can be done with just copy/paste from the original pdf,
and a few "manual" operation
"""


# Parse the equipment list to find characteristics of individual weapons
def parse_equipment(equipment):
    global alljweapons

    nested = 0
    weapons_raw = []
    weapons = []
    namestart = 0
    for index, char in enumerate(equipment):
        if char == '(':
            if nested == 0:
                start = index
            nested += 1
        elif char == ')':
            nested -= 1
            if nested == 0:
                weapons_raw.append((equipment[namestart:start].strip(' ,'), equipment[start + 1:index]))
                namestart = index + 1

    for w in weapons_raw:
        name = w[0]
        wprange = 0
        armorPiercing = 0
        attacks = 0
        special = []
        count = 1

        for c in w[1].split(','):
            c = c.strip()
            if c.endswith('"'):
                wprange = int(c[:-1])
            elif c.startswith('AP'):
                armorPiercing = int(c[3:-1])
            elif c.startswith('A') and c[1:].isdigit():
                attacks = int(c[1:])
            else:
                special.append(c.strip())

        weapons.append(name)

        # remove 2x from the weapon name
        firstword = name.split()[0]
        if firstword.endswith('x'):
            if firstword[:-1].isdigit():
                name = name[len(firstword) + 1:]

        # remove Linked from weapon name
        if name.split()[0] == 'Linked':
            if 'Linked' in special:
                special.remove('Linked')
            name = ' '.join(name.split()[1:])

        name = '"' + name + '"'
        if name not in alljweapons:
            alljweapons[name] = OrderedDict([('range', wprange), ('attacks', attacks), ('ap', armorPiercing), ('special', special)])

    return weapons


def parse_upgrades(upgrades):
    tmp = [up.strip() for up in upgrades.split(',')]
    return [up for up in tmp if up != '-']


def parse_special(special):
    special = special.split(',')
    # strip all whitespace
    return [sp.strip() for sp in special]


def parse_units(name, data):
    global alljweapons
    column_order = ['name', 'count', 'qua', 'def', 'equipment', 'special', 'upgrades']
    alljunits = []
    for row in data[1:]:
        dunit = {}
        if len(row) < len(column_order):
            continue

        for i, col in enumerate(column_order):
            dunit[col] = row[i]

        equipment = parse_equipment(dunit['equipment'])

        ju = OrderedDict([('name', dunit['name']), ('count', dunit['count']), ('quality', dunit['qua']), ('defense', dunit['def']), ('equipment', equipment), ('special', parse_special(dunit['special'])), ('upgrades', parse_upgrades(dunit['upgrades']))])
        alljunits.append(ju)

    with open(name + '.json', 'w') as f:
        f.write(json.dumps(alljunits, indent=2))


def parse_weapons(data):
    for row in data:
        parse_equipment(row[0])


def main():
    global alljweapons

    parser = argparse.ArgumentParser(description='Parse ods file to help import pdf into json')
    parser.add_argument('fname', metavar='fname', type=str,
                        help='file to parse')

    args = parser.parse_args()

    data = get_data(args.fname)

    alljweapons = {}
    unitpage = 1

    for sheet in data:
        if sheet.startswith('units'):
            parse_units(sheet, data[sheet])

        else:
            parse_weapons(data[sheet])

    with open('equipments.json', 'w') as f:
        f.write('{"weapons" : {\n')
        f.write(',\n'.join(['{:<30} : '.format(k) + json.dumps(alljweapons[k]) for k in alljweapons]))
        f.write('\n}, "wargear" : {\n')
        f.write('\n}, "factionRules" : {\n}}\n')


if __name__ == "__main__":
    # execute only if run as a script
    main()
