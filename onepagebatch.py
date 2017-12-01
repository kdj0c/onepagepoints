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


from onepagepoints import *
import yaml
import os
import copy
import argparse
from collections import OrderedDict


# Get hardcoded cost for per-faction special rules.
def getFactionCost(unit):
    global factionRules

    return sum([factionRules[r] for r in unit.specialRules + unit.wargearSp if r in factionRules])


# return pretty string for points
def points(n):
    if n == 0:
        return "Free"
    if n == 1:
        return "1 pt"
    return '{} pts'.format(n)


# return pretty string for duplicates weapons
def pCount(n):
    if n < 2:
        return ''
    return '{}x '.format(n)


# Return unit name and count if more than one
def prettyName(unit):
    if unit.count > 1:
        return unit.name + ' [{0}]'.format(unit.count)
    return unit.name


# Latex uses ~ to prevent line break
def no_line_break(s):
    return s.replace(' ', '~')


def prettyProfile(equipment):
    if isinstance(equipment, Weapon):
        return no_line_break(equipment.Profile())
    return equipment.Profile()


# Return a pretty string for latex of the list of equipments
def PrettyEquipmentsTex(equipments):
    equWithCount = list(OrderedDict.fromkeys([(equ, equipments.count(equ)) for equ in equipments]))
    return [pCount(c) + no_line_break(e.name) + ' ' + prettyProfile(e) for e, c in equWithCount]


# Return a pretty string of the list of equipments
def PrettyEquipments(equipments):
    equWithCount = list(OrderedDict.fromkeys([(equ, equipments.count(equ)) for equ in equipments]))
    return [pCount(c) + e.name + ' ' + e.Profile() for e, c in equWithCount]


class Upgrade:
    def __init__(self, batch):
        self.all = batch.get('all', False)
        self.text = batch['text']
        self.preremove = batch.get('pre-remove', {})
        self.preadd = batch.get('pre-add', {})
        self.remove = batch.get('remove', {})
        self.add = batch['add']
        self.rawcost = []

    # Calculate the cost of an upgrade on a unit
    # If the upgrade is only for one model, set the unit count to 1
    # remove equipment, add new equipment and calculate the new cost.
    def Cost_unit(self, unit):
        global armory

        base_unit = copy.copy(unit)
        if not self.all:
            base_unit.SetCount(1)

        base_unit.RemoveEquipments(armory.get(self.preremove))
        base_unit.AddEquipments(armory.get(self.preadd))
        prev_cost = base_unit.cost + getFactionCost(base_unit)
        base_unit.RemoveEquipments(armory.get(self.remove))

        costs = []
        for upgrade in self.add:
            new_unit = copy.copy(base_unit)
            new_unit.AddEquipments(armory.get(upgrade))

            up_cost = new_unit.cost + getFactionCost(new_unit) - prev_cost
            costs.append(up_cost)

        # print('Cost for unit {}: {}'.format(unit.name, costs))
        return costs

    # an upgrade group cost is calculated for all units who have access to this
    # upgrade group, so calculate the mean
    def Cost(self, units):
        u_count = len(units)
        cost = [0] * len(self.add)
        for unit in units:
            cost = [x + y for x, y in zip(cost, self.Cost_unit(unit))]
        self.cost = [int(round(c / u_count)) for c in cost]
        # print('Cost for all units: {}'.format(self.cost))
        return self.cost


class UpgradeGroup(list):
    def __init__(self, name, ydata):
        self.name = name
        super().__init__([Upgrade(upgrade) for upgrade in ydata])


def get_unit_stat(unit):
    data = ['{0} {1} {2}+'.format(prettyName(unit), str(unit.quality), str(unit.basedefense))]
    data += [', '.join(PrettyEquipments(unit.equipments))]
    data += [", ".join(unit.specialRules)]
    data += [", ".join(unit.upgrades)]
    data += [points(unit.cost + getFactionCost(unit))]
    return '\n'.join([d for d in data if d])


def get_units_stats(units):
    return '\n\n'.join([get_unit_stat(unit) for unit in units])


def get_unit_line(unit):
    cost = unit.cost + getFactionCost(unit)
    equ = ", ".join(['\mbox{' + e + '}' for e in PrettyEquipmentsTex(unit.equipments)])
    sp = ", ".join(unit.specialRules)
    up = ", ".join(unit.upgrades)
    return ' & '.join([prettyName(unit), str(unit.quality), str(unit.basedefense) + '+', equ, sp, up, points(cost)])


def get_units_tex(units):
    return '\\\\ \n'.join([get_unit_line(unit) for unit in units])


def get_units_txt(units):
    return '\n'.join([get_unit_line(unit) for unit in units])


def get_upgrade_linetxt(equ, cost):
    global armory
    return ', '.join(PrettyEquipments(armory.get(equ))) + ' ' + points(cost)


def get_upgrade_grouptxt(group, upgrades):
    data = ''
    preamble = group + ' | '

    ret = []
    for up in upgrades:
        ret += [preamble + up.text + ':']
        ret += [get_upgrade_linetxt(addEqu, up.cost[i]) for i, addEqu in enumerate(up.add)]
        preamble = ''
    return data + '\n'.join(ret) + '\n'


def get_upgrade_txt(upgrades):
    return '\n'.join([get_upgrade_grouptxt(group.name, group) for group in upgrades])


def get_upgrade_line(equ, cost):
    global armory
    return ', '.join(PrettyEquipmentsTex(armory.get(equ))) + ' & ' + points(cost)


def get_upgrade_group(group, upgrades):

    data = '\\UpgradeTable{ '
    preamble = group + ' | '

    ret = []
    for up in upgrades:
        ret += ['\\multicolumn{2}{p{\\dimexpr \\linewidth - 2pt \\relax}}{\\bf ' + preamble + up.text + ': } ']
        ret += [get_upgrade_line(addEqu, up.cost[i]) for i, addEqu in enumerate(up.add)]
        preamble = ''
    return data + ' \\\\ \n'.join(ret) + '}\n'


def get_upgrade_tex(upgrades):
    return ''.join([get_upgrade_group(group.name, group) for group in upgrades])


def write_file(filename, path, data):
    fname = os.path.join(path, filename)
    with open(fname, "w") as f:
        print('  Writing {}'.format(fname))
        f.write(data)


def read_yaml(filename, path):
    fname = os.path.join(path, filename)
    with open(fname, "r") as f:
        print('  Processing {}'.format(fname))
        return yaml.load(f.read())


def generateFaction(faction, txtdir):
    global armory
    global factionRules

    armory = Armory()

    if os.path.exists(os.path.join('Common', 'equipments.yml')):
        jequipments = read_yaml('equipments.yml', 'Common')
        armory.add([Weapon(name, w.get('range', 0), w['attacks'], w.get('ap', 0), w.get('special', [])) for name, w in jequipments['weapons'].items()])

    jequipments = read_yaml("equipments.yml", faction)
    armory.add([Weapon(name, w.get('range', 0), w['attacks'], w.get('ap', 0), w.get('special', [])) for name, w in jequipments['weapons'].items()])
    armory.add([WarGear(name, wargear.get('special', []), armory.get(wargear.get('weapons', [])), wargear.get('text', '')) for name, wargear in jequipments['wargear'].items()])

    factionRules = jequipments['factionRules']

    allFiles = os.listdir(faction)
    data_txt = ''

    for i in ['', 1, 2, 3, 4, 5]:
        unitFile = 'units' + str(i) + '.yml'
        upgradeFile = 'upgrades' + str(i) + '.yml'
        if unitFile in allFiles and upgradeFile in allFiles:
            yunits = read_yaml(unitFile, faction)
            yupgrades = read_yaml(upgradeFile, faction)

            units = [Unit.from_dict(yunit, armory) for yunit in yunits]
            upgrades = [UpgradeGroup(group, up_group) for group, up_group in yupgrades.items()]

            for group in upgrades:
                affected_units = [unit for unit in units if group.name in unit.upgrades]
                for upgrade in group:
                    upgrade.Cost(affected_units)

            write_file(unitFile[:-3] + 'tex', faction, get_units_tex(units))
            write_file(upgradeFile[:-3] + 'tex', faction, get_upgrade_tex(upgrades))

            data_txt += '\n\n' + get_units_stats(units)
            data_txt += '\n\n' + get_upgrade_txt(upgrades)

    if txtdir == '':
        txtdir = faction
    write_file(faction + '.txt', txtdir, data_txt)


def main():
    parser = argparse.ArgumentParser(description='This script will compute the Unit costs and upgrade costs for a faction, and write the .tex files for LaTeX')
    parser.add_argument('-t', '--txt-dir', type=str, default='',
                        help='directory to write the txt files, used for diff between releases')
    parser.add_argument('path', type=str, nargs='+',
                        help='path to the faction (should contain at list equipments.yml, units1.yml, upgrades1.yml)')

    args = parser.parse_args()

    for faction in args.path:
        print("Building faction {}".format(faction))
        generateFaction(faction, args.txt_dir)


if __name__ == "__main__":
    # execute only if run as a script
    main()
