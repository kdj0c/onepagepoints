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
import json
import os
import copy
import argparse
from collections import OrderedDict


def getFactionCost(unit):
    global factionRules

    return sum([factionRules[r] for r in unit.specialRules + unit.wargearSp if r in factionRules])


def points(n):
    if n == 0:
        return "Free"
    if n == 1:
        return "1 pt"
    return '{} pts'.format(n)


def pCount(n):
    if n < 2:
        return ''
    return '{}x '.format(n)


def prettyProfile(equipment):
    if isinstance(equipment, Weapon):
        return equipment.Profile().replace(' ', '~')
    return equipment.Profile()


# Return a pretty string for latex of the list of equipments
# And prefix with 2x if the equipment is present twice.
def prettyEquipments(equipments):
    equWithCount = list(OrderedDict.fromkeys([(equ, equipments.count(equ)) for equ in equipments]))
    return [pCount(c) + e.name.replace(' ', '~') + ' ' + prettyProfile(e) for e, c in equWithCount]


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
            print("Missing upgrade_group {0} in upgrades.json".format(upgrade_group))


def get_unit_line(junit):
    global armory

    unit = Unit.from_dict(junit, armory)
    cost = unit.cost + getFactionCost(unit)
    equ = ", ".join(['\mbox{' + e + '}' for e in prettyEquipments(unit.equipments)])
    sp = ", ".join(unit.specialRules)
    up = ", ".join(junit['upgrades'])
    return '{0};{1};{2};{3};{4};{5};{6};{7}'.format(unit.name, unit.count, unit.quality, unit.basedefense, equ, sp, up, points(cost))


def get_units_csv(junits):
    return '\n'.join([get_unit_line(junit) for junit in junits])


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


def get_upgrade_group(group, upgrades):
    global armory

    data = group + ' | '
    for up in upgrades:
        data += up['text'] + ':;;' + group + '\n'
        cost = calculate_mean_upgrade_cost(up['cost'])
        for i, addEqu in enumerate(up['add']):
            data += '{0};{1};{2}\n'.format(', '.join(prettyEquipments(armory.get(addEqu))), points(cost[i]), group)
    return data


def get_upgrade_csv(jupgrades):
    return ''.join([get_upgrade_group(group, upgrades) for group, upgrades in jupgrades.items()])


def write_csv(filename, path, data):
    fname = os.path.join(path, filename)
    with open(fname, "w") as f:
        print('  Writing {}'.format(fname))
        f.write(data)


def read_json(filename, path):
    fname = os.path.join(path, filename)
    with open(fname, "r") as f:
        print('  Processing {}'.format(fname))
        return json.loads(f.read())


def generateFaction(faction):
    global armory
    global factionRules

    armory = Armory()

    if os.path.exists(os.path.join('Common', 'equipments.json')):
        jequipments = read_json('equipments.json', 'Common')
        armory.add([Weapon(name, w['range'], w['attacks'], w['ap'], w['special']) for name, w in jequipments['weapons'].items()])

    jequipments = read_json("equipments.json", faction)
    armory.add([Weapon(name, w['range'], w['attacks'], w['ap'], w['special']) for name, w in jequipments['weapons'].items()])
    armory.add([WarGear(name, wargear.get('special', []), armory.get(wargear.get('weapons', [])), wargear.get('text', '')) for name, wargear in jequipments['wargear'].items()])

    factionRules = jequipments['factionRules']

    allFiles = os.listdir(faction)

    for i in ['', 1, 2, 3, 4, 5]:
        unitFile = 'units' + str(i) + '.json'
        upgradeFile = 'upgrades' + str(i) + '.json'
        if unitFile in allFiles and upgradeFile in allFiles:
            junits = read_json(unitFile, faction)
            jupgrades = read_json(upgradeFile, faction)

            for junit in junits:
                calculate_unit_cost(junit, jupgrades)

            write_csv(unitFile[:-4] + 'csv', faction, get_units_csv(junits))
            write_csv(upgradeFile[:-4] + 'csv', faction, get_upgrade_csv(jupgrades))


def main():
    parser = argparse.ArgumentParser(description='This script will compute the Unit costs and upgrade costs for a faction, and write the .csv files for LaTeX')
    parser.add_argument('path', metavar='path', type=str, nargs='+',
                        help='path to the faction (should contain at list equipments.json, units1.json, upgrades1.json)')

    args = parser.parse_args()

    for faction in args.path:
        print("Building faction {}".format(faction))
        generateFaction(faction)


if __name__ == "__main__":
    # execute only if run as a script
    main()
