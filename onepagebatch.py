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


class DumpTxt:
    def __init__(self):
        self.data = []

    def _addUnit(self, unit):
        data = ['{0} {1} {2}+'.format(prettyName(unit), str(unit.quality), str(unit.basedefense))]
        data += [', '.join(PrettyEquipments(unit.equipments))]
        data += [", ".join(unit.specialRules)]
        data += [", ".join(unit.upgrades)]
        data += [points(unit.cost + getFactionCost(unit))]
        return '\n'.join([d for d in data if d])

    def addUnits(self, units):
        self.data += [self._addUnit(unit) for unit in units]

    def _getUpLine(self, equ, cost):
        global armory
        return ', '.join(PrettyEquipments(armory.get(equ))) + ' ' + points(cost)

    def _getUpGroup(self, group, upgrades):
        data = ''
        preamble = group + ' | '

        ret = []
        for up in upgrades:
            ret += [preamble + up.text + ':']
            ret += [self._getUpLine(addEqu, up.cost[i]) for i, addEqu in enumerate(up.add)]
            preamble = ''
        return data + '\n'.join(ret)

    def addUpgrades(self, upgrades):
        self.data += [self._getUpGroup(group.name, group) for group in upgrades]

    def getTxt(self):
        return '\n\n'.join(self.data)


class DumpTex:
    # Latex uses ~ to prevent line break
    def no_line_break(self, s):
        return s.replace(' ', '~')

    def prettyProfile(self, equipment):
        if isinstance(equipment, Weapon):
            return self.no_line_break(equipment.Profile())
        return equipment.Profile()

    # Return a pretty string for latex of the list of equipments
    def PrettyEquipments(self, equipments):
        equWithCount = list(OrderedDict.fromkeys([(equ, equipments.count(equ)) for equ in equipments]))
        return [pCount(c) + self.no_line_break(e.name) + ' ' + self.prettyProfile(e) for e, c in equWithCount]

    def _getUnit(self, unit):
        cost = unit.cost + getFactionCost(unit)
        equ = ", ".join(['\mbox{' + e + '}' for e in self.PrettyEquipments(unit.equipments)])
        sp = ", ".join(unit.specialRules)
        up = ", ".join(unit.upgrades)
        return ' & '.join([prettyName(unit), str(unit.quality), str(unit.basedefense) + '+', equ, sp, up, points(cost)])

    def getUnits(self, units):
        return '\\\\ \n'.join([self._getUnit(unit) for unit in units])

    def _getUpLine(self, equ, cost):
        global armory
        return ', '.join(self.PrettyEquipments(armory.get(equ))) + ' & ' + points(cost)

    def _getUpGroup(self, group, upgrades):
        data = '\\UpgradeTable{ '
        preamble = group + ' | '
        ret = []
        for up in upgrades:
            ret += ['\\multicolumn{2}{p{\\dimexpr \\linewidth - 2pt \\relax}}{\\bf ' + preamble + up.text + ': } ']
            ret += [self._getUpLine(addEqu, up.cost[i]) for i, addEqu in enumerate(up.add)]
            preamble = ''
        return data + ' \\\\ \n'.join(ret) + '}\n'

    def getUpgrades(self, upgrades):
        return ''.join([self._getUpGroup(group.name, group) for group in upgrades])


class DumpHtml:
    def __init__(self):
        with open('Template/header.html') as f:
            self.header = f.read()
        with open('Template/footer.html') as f:
            self.footer = f.read()
        self.data = ""

    def no_line_break(self, s):
        return s.replace(' ', '&nbsp;')

    def points(self, n):
        return self.no_line_break(points(n))

    def to_cells(self, cells):
        return '\n'.join(['    <td>' + cell + '</td>' for cell in cells])

    def to_hdr(self, cells):
        return '\n'.join(['    <th>' + cell + '</th>' for cell in cells])

    def to_row(self, rows):
        return '\n'.join(['  <tr>\n' + row + '\n  </tr>' for row in rows])

    def _getUnit(self, unit):
        data = [prettyName(unit), str(unit.quality), str(unit.basedefense) + '+']
        data += [',<br> '.join(PrettyEquipments(unit.equipments))]
        data += [", ".join(unit.specialRules)]
        data += [", ".join(unit.upgrades)]
        data += [self.points(unit.cost + getFactionCost(unit))]
        return self.to_cells(data)

    def getUnits(self, units):
        table_header = ['Name [size]', 'Qua', 'Def', 'Equipment', 'Special Rules', 'Upgrades', 'Cost']
        self.data += '<br>\n<table>\n'
        rows = [self.to_hdr(table_header)]
        rows.extend([self._getUnit(unit) for unit in units])
        self.data += self.to_row(rows)
        self.data += '</table>\n'

    def _getUpLine(self, equ, cost):
        global armory
        return self.to_cells(PrettyEquipments(armory.get(equ)) + [self.points(cost)])

    def _getUpGroup(self, group, upgrades):
        preamble = group + ' | '

        ret = []
        for up in upgrades:
            ret.append(self.to_hdr([preamble + up.text + ':', '']))
            ret.extend([self._getUpLine(addEqu, up.cost[i]) for i, addEqu in enumerate(up.add)])
            preamble = ''
        return '<br>\n<table class=ut1>\n' + self.to_row(ret) + '\n</table>\n'

    def addUpgrades(self, upgrades):
        self.data += '\n'.join([self._getUpGroup(group.name, group) for group in upgrades])

    def getHtml(self):
        return self.header + self.data + self.footer


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
        yequipments = read_yaml('equipments.yml', 'Common')
        armory.add([Weapon(name, **w) for name, w in yequipments['weapons'].items()])

    yequipments = read_yaml("equipments.yml", faction)
    armory.add([Weapon(name, **w) for name, w in yequipments['weapons'].items()])
    armory.add([WarGear.from_dict(name, wargear, armory) for name, wargear in yequipments['wargear'].items()])

    factionRules = yequipments['factionRules']

    allFiles = os.listdir(faction)
    txt = DumpTxt()
    tex = DumpTex()
    html = DumpHtml()

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

            write_file(unitFile[:-3] + 'tex', faction, tex.getUnits(units))
            write_file(upgradeFile[:-3] + 'tex', faction, tex.getUpgrades(upgrades))

            html.getUnits(units)
            html.addUpgrades(upgrades)
            txt.addUnits(units)
            txt.addUpgrades(upgrades)

    if txtdir == '':
        txtdir = faction
    write_file(faction + '.txt', txtdir, txt.getTxt())
    write_file(faction + '.html', 'out', html.getHtml())


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
