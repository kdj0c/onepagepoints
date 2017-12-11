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

import os
import yaml
import argparse
from collections import OrderedDict

"""
This scripts helps to indent the yaml files for each faction
equipments.yml (list of weapons and wargear)
faction.yml (list of psychics and special rules)
unitsX.yml (list of units for page X)
upgradesX.yml (list of upgrades available for each unit in page X)
"""


class YamlUnit(dict):
    def to_omap(self):
        order = ["name", "count", "quality", "defense", "equipment", "special", "upgrades"]
        return [(key, self[key]) for key in order]


class YamlUpgrade(dict):
    def to_omap(self):
        order = ["text", "all", "pre-remove", "pre-add", "remove", "add"]
        return [(key, self[key]) for key in order if key in self]


class YamlEquipments(dict):
    def to_omap(self):
        order = ["weapons", "wargear", "factionRules"]
        return [(key, self[key]) for key in order if key in self]


class YamlWeapon(dict):
    def to_omap(self):
        order = ["range", "attacks", "ap", "special"]
        return [(key, self[key]) for key in order if key in self and self[key]]


class YamlFactionRules(dict):
    def to_omap(self):
        return [(key, self[key]) for key in self]


class YamlFaction(dict):
    def to_omap(self):
        data = [('title', self.pop('title'))]
        return data + [(key, self[key]) for key in sorted(self)]


def represent_omap(dumper, data):
    return dumper.represent_mapping(u'tag:yaml.org,2002:map', data.to_omap())


def represent_omap_flow(dumper, data):
    return dumper.represent_mapping(u'tag:yaml.org,2002:map', data.to_omap(), flow_style=False)


def format_faction(data):
    yaml.add_representer(YamlFaction, represent_omap)
    newdata = YamlFaction(data)
    return yaml.dump(newdata, default_flow_style=False)


def format_equipments(data):
    yaml.add_representer(YamlEquipments, represent_omap)
    yaml.add_representer(YamlWeapon, represent_omap_flow)
    yaml.add_representer(YamlFactionRules, represent_omap_flow)

    data["weapons"] = {k: YamlWeapon(v) for k, v in data["weapons"].items()}
    data["factionRules"] = YamlFactionRules(data["factionRules"])

    newdata = YamlEquipments(data)

    return yaml.dump(newdata)


def format_units(data):
    yaml.add_representer(YamlUnit, represent_omap)

    newdata = [YamlUnit(unit) for unit in data]
    return yaml.dump(newdata)


def format_upgrades(data):
    yaml.add_representer(YamlUpgrade, represent_omap)
    newdata = {}
    for group, gdata in data.items():
        newdata[group] = [YamlUpgrade(up) for up in gdata]

    return yaml.dump(newdata)


def format_file(filename, path, format_func):
    floc = os.path.join(path, filename)
    print('processing {0}'.format(floc))
    with open(floc, "r") as f:
        rawdata = f.read()
        data = yaml.load(rawdata)

    newdata = format_func(data)

    if newdata != rawdata:
        os.rename(floc, floc + '~')
        with open(floc, "w") as f:
            f.write(newdata)


def indent(faction):
    yamlFiles = [f for f in os.listdir(faction) if f.endswith('.yml')]
    for f in yamlFiles:
        if f == 'equipments.yml':
            format_file(f, faction, format_equipments)
        elif f == 'faction.yml':
            format_file(f, faction, format_faction)
        elif f.startswith('unit'):
            format_file(f, faction, format_units)
        elif f.startswith('upgrades'):
            format_file(f, faction, format_upgrades)


def main():

    parser = argparse.ArgumentParser(description='Indent the yaml source files, to ease editing them by hand, and avoid to much useless diffs')
    parser.add_argument('path', metavar='path', type=str, nargs='+',
                        help='path to the faction to indent all yaml')

    args = parser.parse_args()

    for path in args.path:
        indent(path)


if __name__ == "__main__":
    # execute only if run as a script
    main()
