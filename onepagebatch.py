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
    def __init__(self, batch, faction):
        armory = faction.armory
        self.getFactionCost = faction.getFactionCost
        self.all = batch.get('all', False)
        self.text = batch['text']
        self.preremove = armory.get(batch.get('pre-remove', {}))
        self.preadd = armory.get(batch.get('pre-add', {}))
        self.remove = armory.get(batch.get('remove', {}))
        self.add = [armory.get(up_add) for up_add in batch['add']]
        self.rawcost = []

    # Calculate the cost of an upgrade on a unit
    # If the upgrade is only for one model, set the unit count to 1
    # remove equipment, add new equipment and calculate the new cost.
    def Cost_unit(self, unit):
        base_unit = copy.copy(unit)
        if not self.all:
            base_unit.SetCount(1)

        base_unit.RemoveEquipments(self.preremove)
        base_unit.AddEquipments(self.preadd)
        base_unit.SetFactionCost(self.getFactionCost(base_unit))
        prev_cost = base_unit.cost
        base_unit.RemoveEquipments(self.remove)

        costs = []
        for upgrade in self.add:
            new_unit = copy.copy(base_unit)
            new_unit.AddEquipments(upgrade)
            new_unit.SetFactionCost(self.getFactionCost(new_unit))

            up_cost = new_unit.cost - prev_cost
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
    def __init__(self, name, ydata, faction):
        self.name = name
        super().__init__([Upgrade(upgrade, faction) for upgrade in ydata])


class Faction():
    def __init__(self, name):
        global armory
        self.name = name
        self.armory = Armory()
        armory = self.armory
        self.pages = []
        self._parse_yaml()

    def _read_yaml(self, filename, path):
        fname = os.path.join(path, filename)
        with open(fname, "r") as f:
            print('  Processing {}'.format(fname))
            return yaml.load(f.read())

    def _parse_yaml(self):
        yfaction = self._read_yaml('faction.yml', self.name)
        self.title = yfaction['title']

        if os.path.exists(os.path.join('Common', 'equipments.yml')):
            yequipments = self._read_yaml('equipments.yml', 'Common')
            self.armory.add([Weapon(name, **w) for name, w in yequipments['weapons'].items()])

        yequipments = self._read_yaml("equipments.yml", self.name)
        self.armory.add([Weapon(name, **w) for name, w in yequipments['weapons'].items()])
        self.armory.add([WarGear.from_dict(name, wargear, self.armory) for name, wargear in yequipments['wargear'].items()])

        self.factionRules = yequipments['factionRules']

        allFiles = os.listdir(self.name)

        for i in ['', '1', '2', '3', '4', '5']:
            unitFile = 'units' + i + '.yml'
            upgradeFile = 'upgrades' + i + '.yml'
            if unitFile in allFiles and upgradeFile in allFiles:
                yunits = self._read_yaml(unitFile, self.name)
                yupgrades = self._read_yaml(upgradeFile, self.name)

                units = [Unit.from_dict(yunit, self.armory) for yunit in yunits]
                upgrades = [UpgradeGroup(group, up_group, self) for group, up_group in yupgrades.items()]

                for unit in units:
                    unit.SetFactionCost(self.getFactionCost(unit))

                for group in upgrades:
                    affected_units = [unit for unit in units if group.name in unit.upgrades]
                    for upgrade in group:
                        upgrade.Cost(affected_units)
                spRules = yfaction.get('specialRules' + i, None)
                psychics = yfaction.get('psychics' + i, None)
                self.pages.append((units, upgrades, spRules, psychics))

    # Get hardcoded cost for per-faction special rules.
    def getFactionCost(self, unit):
        return sum([self.factionRules[r] for r in unit.specialRules + unit.wargearSp if r in self.factionRules])


class DumpTxt:
    def __init__(self):
        self.data = []

    def _addUnit(self, unit):
        data = ['{0} {1} {2}+'.format(prettyName(unit), str(unit.quality), str(unit.basedefense))]
        data += [', '.join(PrettyEquipments(unit.equipments))]
        data += [", ".join(unit.specialRules)]
        data += [", ".join(unit.upgrades)]
        data += [points(unit.cost)]
        return '\n'.join([d for d in data if d])

    def addUnits(self, units):
        self.data += [self._addUnit(unit) for unit in units]

    def _getUpLine(self, equ, cost):
        return ', '.join(PrettyEquipments(equ)) + ' ' + points(cost)

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

    def getTxt(self, faction):
        for units, upgrades, specialRules, psychics in faction.pages:
            self.addUnits(units)
            self.addUpgrades(upgrades)
        return '\n\n'.join(self.data)


class DumpTex:
    def __init__(self):
        with open('Template/header.tex') as f:
            self.header = f.read()

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

    def _addUnit(self, unit):
        cost = unit.cost
        equ = ", ".join(['\mbox{' + e + '}' for e in self.PrettyEquipments(unit.equipments)])
        sp = ", ".join(unit.specialRules)
        up = ", ".join(unit.upgrades)
        return ' & '.join([prettyName(unit), str(unit.quality), str(unit.basedefense) + '+', equ, sp, up, points(cost)])

    def addUnits(self, units):
        self.data += '\\UnitTable{'
        self.data += '\\\\ \n'.join([self._addUnit(unit) for unit in units])
        self.data += '}\n'

    def _getUpLine(self, equ, cost):
        return ', '.join(self.PrettyEquipments(equ)) + ' & ' + points(cost)

    def _getUpGroup(self, group, upgrades):
        data = '\\UpgradeTable{ '
        preamble = group + ' | '
        ret = []
        for up in upgrades:
            ret += ['\\multicolumn{2}{p{\\dimexpr \\linewidth - 2pt \\relax}}{\\bf ' + preamble + up.text + ': } ']
            ret += [self._getUpLine(addEqu, up.cost[i]) for i, addEqu in enumerate(up.add)]
            preamble = ''
        return data + ' \\\\ \n'.join(ret) + '}\n'

    def addUpgrades(self, upgrades):
        self.data += ''.join([self._getUpGroup(group.name, group) for group in upgrades])

    def addSpecialRules(self, sp):
        if not sp:
            return
        self.data += '\\specialrules\n'
        self.data += '\n'.join(['\\sprule{' + k + '}{' + v + '}' for k, v in sp.items()]) + '\n'

    def addPsychics(self, psychics):
        if not psychics:
            return
        self.data += '\\startpsychic{\n'
        for quality, spells in psychics.items():
            self.data += '\n'.join(['\\psychic{' + k + '}{' + str(quality) + '+}{' + v + '}\n' for k, v in spells.items()])
        self.data += '}\n'

    def getTex(self, faction):
        self.data = '\\mytitle{' + faction.title + '}\n'
        self.data += '\\begin{document}\n'
        for units, upgrades, specialRules, psychics in faction.pages:
            self.addUnits(units)
            self.data += '\\begin{multicols*}{3}[]\n'
            self.addUpgrades(upgrades)
            self.addSpecialRules(specialRules)
            self.addPsychics(psychics)
            self.data += '\\end{multicols*}\n'
            self.data += '\\pagebreak\n'
        self.data += '\\end{document}'

        return self.header + self.data


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

    def to_li(self, lis):
        return '\n'.join([' <li>\n' + li + '\n </li>' for li in lis])

    def _addUnit(self, unit):
        data = [prettyName(unit), str(unit.quality), str(unit.basedefense) + '+']
        data += [',<br> '.join(PrettyEquipments(unit.equipments))]
        data += [", ".join(unit.specialRules)]
        data += [", ".join(unit.upgrades)]
        data += [self.points(unit.cost)]
        return self.to_cells(data)

    def addUnits(self, units):
        table_header = ['Name [size]', 'Qua', 'Def', 'Equipment', 'Special Rules', 'Upgrades', 'Cost']
        self.data += '<table>\n'
        rows = [self.to_hdr(table_header)]
        rows.extend([self._addUnit(unit) for unit in units])
        self.data += self.to_row(rows)
        self.data += '</table>\n'

    def _getUpLine(self, equ, cost):
        return self.to_cells(PrettyEquipments(equ) + [self.points(cost)])

    def _getUpGroup(self, group, upgrades):
        preamble = group + ' | '

        ret = []
        for up in upgrades:
            ret.append(self.to_hdr([preamble + up.text + ':', '']))
            ret.extend([self._getUpLine(addEqu, up.cost[i]) for i, addEqu in enumerate(up.add)])
            preamble = ''
        return '<table class=ut1>\n' + self.to_row(ret) + '\n</table>\n'

    def addUpgrades(self, upgrades):
        self.data += '<ul>\n'
        self.data += self.to_li([self._getUpGroup(group.name, group) for group in upgrades])
        self.data += '</ul>\n'

    def getHtml(self, faction):
        self.data += '<h1>Grimdark Future ' + faction.title + '</h1>'
        for units, upgrades, specialRules, psychics in faction.pages:
            self.addUnits(units)
            self.addUpgrades(upgrades)

        return self.header + self.data + self.footer


def write_file(filename, path, data):
    fname = os.path.join(path, filename)
    with open(fname, "w") as f:
        print('  Writing {}'.format(fname))
        f.write(data)


def generateFaction(factionName):
    faction = Faction(factionName)

    write_file(factionName + '.txt', 'out/txt', DumpTxt().getTxt(faction))
    write_file(factionName + '.html', 'out', DumpHtml().getHtml(faction))
    write_file(factionName + '.tex', 'out/tex', DumpTex().getTex(faction))


def main():
    parser = argparse.ArgumentParser(description='This script will compute the Unit costs and upgrade costs for a faction, and write the .tex files for LaTeX')
    parser.add_argument('-t', '--txt-dir', type=str, default='',
                        help='directory to write the txt files, used for diff between releases')
    parser.add_argument('path', type=str, nargs='+',
                        help='path to the faction (should contain at list equipments.yml, units1.yml, upgrades1.yml)')

    args = parser.parse_args()

    for faction in args.path:
        faction = faction.strip('/')
        print("Building faction {}".format(faction))
        generateFaction(faction)


if __name__ == "__main__":
    # execute only if run as a script
    main()
