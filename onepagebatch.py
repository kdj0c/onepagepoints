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


# Calculate the cost of an upgrade on a unit
# If the upgrade is only for one model, set the unit count to 1
# remove equipment, add new equipment and calculate the new cost.
def calculate_upgrade_cost(unit, to_preremove, to_preadd, to_remove, to_add, all):
    global armory

    new_unit = copy.copy(unit)
    if not all:
        new_unit.SetCount(1)

    new_unit.RemoveEquipments(armory.get(to_preremove))
    new_unit.AddEquipments(armory.get(to_preadd))

    prev_cost = new_unit.cost + getFactionCost(unit)

    new_unit.RemoveEquipments(armory.get(to_remove))

    costs = []
    for upgrade in to_add:
        add_unit = copy.copy(new_unit)
        add_unit.AddEquipments(armory.get(upgrade))

        up_cost = add_unit.cost + getFactionCost(add_unit) - prev_cost
        costs.append(up_cost)
    return costs


def calculate_upgrade_group_cost(unit, upgrade_group):
    for upgrade_batch in upgrade_group:
        all = upgrade_batch.get('all', False)
        to_preremove = upgrade_batch.get('pre-remove', {})
        to_preadd = upgrade_batch.get('pre-add', {})
        to_remove = upgrade_batch.get('remove', {})
        to_add = upgrade_batch['add']
        costs = calculate_upgrade_cost(unit, to_preremove, to_preadd, to_remove, to_add, all)
        if 'cost' in upgrade_batch:
            upgrade_batch['cost'].append(costs)
        else:
            upgrade_batch['cost'] = [costs]


def calculate_unit_cost(junit, jupgrades):
    global armory

    unit = Unit.from_dict(junit, armory)

    up = junit['upgrades']
    for upgrade_group in junit['upgrades']:
        if upgrade_group in jupgrades:
            calculate_upgrade_group_cost(unit, jupgrades[upgrade_group])
        else:
            print("Missing upgrade_group {0} in upgrades.yml".format(upgrade_group))


# an upgrade group cost is calculated for all units who have access to this
# upgrade group, so calculate the mean
# will transform [[11, 13], [7, 10]] in [9, 12]
def calculate_mean_upgrade_cost(costs):
    count = len(costs)
    ret = [0] * len(costs[0])
    for cu in costs:
        for i, c in enumerate(cu):
            ret[i] += c / count

    ret = [int(round(c)) for c in ret]
    return ret


def get_unit_stat(junit):
    global armory

    unit = Unit.from_dict(junit, armory)
    cost = unit.cost + getFactionCost(unit)

    data = ['{0} {1} {2}+'.format(prettyName(unit), str(unit.quality), str(unit.basedefense))]
    data += [', '.join(PrettyEquipments(unit.equipments))]
    data += [", ".join(unit.specialRules)]
    data += [", ".join(junit['upgrades'])]
    data += [points(cost)]

    return '\n'.join([d for d in data if d])


def get_units_stats(junits):
    return '\n\n'.join([get_unit_stat(junit) for junit in junits])


def get_unit_line(junit):
    global armory

    unit = Unit.from_dict(junit, armory)
    cost = unit.cost + getFactionCost(unit)
    equ = ", ".join(['\mbox{' + e + '}' for e in PrettyEquipmentsTex(unit.equipments)])
    sp = ", ".join(unit.specialRules)
    up = ", ".join(junit['upgrades'])
    return ' & '.join([prettyName(unit), str(unit.quality), str(unit.basedefense) + '+', equ, sp, up, points(cost)])


def get_units_tex(junits):
    return '\\\\ \n'.join([get_unit_line(junit) for junit in junits])


def get_units_txt(junits):
    return '\n'.join([get_unit_line(junit) for junit in junits])


def get_upgrade_linetxt(equ, cost):
    global armory
    return ', '.join(PrettyEquipments(armory.get(equ))) + ' ' + points(cost)


def get_upgrade_grouptxt(group, upgrades):

    data = ''
    preamble = group + ' | '

    ret = []
    for up in upgrades:
        ret += [preamble + up['text'] + ':']
        ret += [get_upgrade_linetxt(addEqu, up['cost'][i]) for i, addEqu in enumerate(up['add'])]
        preamble = ''
    return data + '\n'.join(ret) + '\n'


def get_upgrade_txt(jupgrades):
    return '\n'.join([get_upgrade_grouptxt(group, upgrades) for group, upgrades in jupgrades.items()])


def get_upgrade_line(equ, cost):
    global armory
    return ', '.join(PrettyEquipmentsTex(armory.get(equ))) + ' & ' + points(cost)


def get_upgrade_group(group, upgrades):

    data = '\\UpgradeTable{ '
    preamble = group + ' | '

    ret = []
    for up in upgrades:
        ret += ['\\multicolumn{2}{p{\\dimexpr \\linewidth - 2pt \\relax}}{\\bf ' + preamble + up['text'] + ': } ']
        ret += [get_upgrade_line(addEqu, up['cost'][i]) for i, addEqu in enumerate(up['add'])]
        preamble = ''
    return data + ' \\\\ \n'.join(ret) + '}\n'


def get_upgrade_tex(jupgrades):
    return ''.join([get_upgrade_group(group, upgrades) for group, upgrades in jupgrades.items()])


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
            junits = read_yaml(unitFile, faction)
            jupgrades = read_yaml(upgradeFile, faction)

            for junit in junits:
                calculate_unit_cost(junit, jupgrades)
            for upgrades in jupgrades.values():
                for up in upgrades:
                    up['cost'] = calculate_mean_upgrade_cost(up['cost'])

            write_file(unitFile[:-3] + 'tex', faction, get_units_tex(junits))
            write_file(upgradeFile[:-3] + 'tex', faction, get_upgrade_tex(jupgrades))

            data_txt += '\n\n' + get_units_stats(junits)
            data_txt += '\n\n' + get_upgrade_txt(jupgrades)

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
