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

"""
This scripts helps to indent the json files for each faction
equipments.json (list of weapons and wargear)
unitsX.json (list of units for page X)
upgradesX.json (list of upgrades available for each unit in page X)
"""

import os
import json
import argparse


def format_weapon(w):
    s = '{{ "range" : {:<2}, "attacks" : {:<2}, "ap" : {:<2}, "special" : {}}}'.format(w['range'], w['attacks'], w['ap'], json.dumps(w['special']))
    return s


def format_equipments(jsonFile):
    print('processing {0}'.format(os.path.abspath(jsonFile)))
    with open(jsonFile, "r") as f:
        data = json.loads(f.read())

    os.rename(jsonFile, jsonFile + "~")

    weapons = data['weapons']
    wargear = data['wargear']
    factionrules = data['factionRules']

    with open(jsonFile, "w") as f:
        f.write('{"weapons" : {\n')
        f.write(",\n".join(['{:<30} : '.format('"' + w + '"') + format_weapon(weapons[w]) for w in sorted(weapons)]))
        f.write('\n}, "wargear" : {\n')
        f.write(",\n".join(['{:<30} : '.format('"' + w + '"') + json.dumps(wargear[w]) for w in sorted(wargear)]))
        f.write('\n}, "factionRules" : {\n')
        f.write(",\n".join(['{:<30} : '.format('"' + r + '"') + json.dumps(factionrules[r]) for r in sorted(factionrules)]))
        f.write('\n}}\n')


def format_unit(unit):
    s = '  "name" : "{}",\n'.format(unit['name'])
    s += '  "count" : {},\n'.format(unit['count'])
    s += '  "quality" : {},\n'.format(unit['quality'])
    s += '  "defense" : {},\n'.format(unit['defense'])
    s += '  "equipment" : {},\n'.format(json.dumps(unit['equipment']))
    s += '  "special" : {},\n'.format(json.dumps(unit['special']))
    s += '  "upgrades" : {}\n'.format(json.dumps(unit['upgrades']))
    return s


def format_units(jsonFile):
    print('processing {0}'.format(os.path.abspath(jsonFile)))
    with open(jsonFile, "r") as f:
        data = json.loads(f.read())

    os.rename(jsonFile, jsonFile + "~")

    with open(jsonFile, "w") as f:
        f.write('[{\n')
        f.write('},{\n'.join([format_unit(unit) for unit in data]))
        f.write('}]\n')


def format_batch(batch):
    s = '      "text" : "{}",\n'.format(batch['text'])
    if 'all' in batch and batch['all']:
        s += '      "all" : true,\n'
    if 'remove' in batch:
        s += '      "remove" : {},\n'.format(json.dumps(batch['remove']))
    s += '      "add" : {}\n'.format(json.dumps(batch['add']))
    return s


def format_group(groupName, group):
    s = '"{0}" : [{{\n'.format(groupName)
    s += '    },{\n'.join([format_batch(batch) for batch in group])
    return s


def format_upgrades(jsonFile):
    print('processing {0}'.format(os.path.abspath(jsonFile)))
    with open(jsonFile, "r") as f:
        data = json.loads(f.read())

    os.rename(jsonFile, jsonFile + "~")

    with open(jsonFile, "w") as f:
        f.write('{\n')
        f.write('}],\n'.join([format_group(group, data[group]) for group in sorted(data)]))
        f.write('}]}\n')


def format_faction():
    allFiles = os.listdir(".")

    equFile = 'equipments.json'
    if equFile in allFiles:
        format_equipments(equFile)

    for f in allFiles:
        if f.startswith('units') and f.endswith('.json'):
            format_units(f)
        if f.startswith('upgrades') and f.endswith('.json'):
            format_upgrades(f)


def main():

    parser = argparse.ArgumentParser(description='Indent the json source files, to ease editing them by hand, and avoid to much useless diffs')
    parser.add_argument('path', metavar='path', type=str, nargs='+',
                        help='path to the faction to indent all json')

    args = parser.parse_args()

    current_dir = os.getcwd()
    for path in args.path:
        os.chdir(path)
        format_faction()
        os.chdir(current_dir)


if __name__ == "__main__":
    # execute only if run as a script
    main()
