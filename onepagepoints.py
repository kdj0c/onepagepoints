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

import copy

# Adjust defense and attack cost, to match onepagerules current prices
adjust_defense_cost = 0.8
adjust_attack_cost = 0.8


# Cost per defense point (2+ => 6, 6+ => 24, 10+ => 58)
def defense_cost(d):
    return (d * d + d + 6.0) / 2.0


# defense cost multiplier (higher quality units are tougher, due to moral test)
# 1 for 2+ quality, 0.6 for 6+ quality
def quality_defense_factor(q):
    return 1.0 - 0.1 * (q - 2.0)


# Attack cost multiplier, probability to hit according to quality
# 5/6 for 2+, 1/6 for 6+
def quality_attack_factor(q):
    return (7.0 - q) / 6.0


# AP cost multiplier.
# 1 for no AP, * 1.2 for each AP point
def ap_cost(ap):
    return (1.2 ** ap)


# Range cost multiplier.
# melee threaten range is charge distance (12" = speed)
# guns threaten range is advance distance (6" = speed/2) + weapon range
def range_cost(wrange, speed):
    if wrange == 0:
        c = speed ** 0.75
    else:
        c = (wrange + speed / 2) ** 0.75
    return c


# WargGear can include special rules for model, and weapons
# Like a jetbike gives "fast" rules and a Linked ShardGun
class WarGear:
    def __init__(self, name='Unknown Gear', specialRules=[], weapons=[]):
        self.name = name
        self.specialRules = specialRules
        self.weapons = weapons

    def __str__(self):
        s = self.name + ' ('
        s += ', '.join(self.specialRules + [str(w) for w in self.weapons])
        return s + ')'

    def Cost(self, speed, quality):
        cost = 0
        for w in self.weapons:
            cost += w.Cost(speed, quality)
        return cost


# Class for weapons
class Weapon:
    def __init__(self, name='Unknown Weapon', range=0, attacks=0, armorPiercing=0, weaponRules=[]):
        self.name = name
        self.range = range
        self.attacks = attacks
        self.armorPiercing = armorPiercing
        self.weaponRules = weaponRules
        self.specialRules = []
        self.cost = 0

    def __repr__(self):
        return "{0}({1})".format(self.name, self.__dict__)

    def __str__(self):
        s = self.name + ' ('
        if self.range > 0:
            s += '{0}", '.format(self.range)
        s += 'A{0}'.format(self.attacks)
        if self.armorPiercing:
            s += ', AP({0})'.format(self.armorPiercing)
        if self.weaponRules:
            s += ', ' + ', '.join(self.weaponRules)
        s += ')'
        return s

    def Pretty(self):
        if self.cost:
            s = str(self.cost) + " pts "
        else:
            s = ''
        s += self.__str__()
        return s

    def Cost(self, speed, quality):
        sfactor = 1
        simpact = 0
        rending = 0
        wrange = self.range
        ap = self.armorPiercing

        for s in self.weaponRules:
            if s == 'Deadly':
                sfactor *= 2.5
            elif s == 'Linked':
                quality -= 1
            elif s == 'Rending':
                # rending is 1/6 of having AP(8)
                rending = (1 / 6) * (ap_cost(8) - ap_cost(self.armorPiercing))
            elif s.startswith('Blast'):
                sfactor *= int(s[6:-1])
            elif s.startswith('Impact'):
                simpact = int(s[7:-1])
            elif s == 'Autohit':
                quality = 1
            elif s == 'Limited':
                sfactor /= 2
            elif s == 'Sniper':
                # Sniper is 2+ hit and ignore cover (so statistically half an ap)
                quality = 2
                ap += 0.5
            elif s == 'Indirect':
                wrange *= 1.4

        self.cost = sfactor * self.attacks * range_cost(wrange, speed) * (ap_cost(ap) * quality_attack_factor(quality) + rending)
        # Impact weapon have automatic hit, but only when charging (so 0.5 cost of the same weapon without quality factor)
        if simpact:
            self.cost += 0.5 * simpact * sfactor * ap_cost(ap) * range_cost(wrange, speed)

        self.cost = int(round(self.cost * adjust_attack_cost))

        return self.cost


class Armory(dict):
    # Armory class is a dictionnary of all Weapons and WarGear for a faction.
    def __init__(self, *args):
        dict.__init__(self, args)

    def getOne(self, name):
        if name in self:
            return self[name]

        if name.endswith('s'):
            singular = name[:-1]
            if singular in self:
                self[name] = copy.copy(self[singular])
                self[name].name = name
                return self[name]

        print('Error equipment {0} Not found !'.format(name))
        return None

# Return the list of equipments objects, from their names.
# if the name start with "2x ", return twice the same object in the list.
    def get(self, names):
        for name in names:
            if ' ' in name:
                firstword, remaining = name.split(' ', 1)
                if firstword.endswith('x') and firstword[:-1].isdigit():
                    n = int(firstword[:-1])
                    position = names.index(name)
                    names.remove(name)
                    for i in range(n):
                        names.insert(position, remaining)

        return [self.getOne(name) for name in names]

    def add(self, equipments):
        for equipment in equipments:
            self[equipment.name] = equipment

            if isinstance(equipment, Weapon):
                if equipment.range > 0 and not 'Linked' in equipment.specialRules:
                    name = 'Linked ' + equipment.name
                    self[name] = Weapon(name, equipment.range, equipment.attacks, equipment.armorPiercing, ['Linked'] + equipment.weaponRules)


class Unit:
    def __init__(self, name='Unknown Unit', count=1, quality=4, defense=2, equipments=[], specialRules=[]):
        self.name = name
        self.specialRules = specialRules
        self.equipments = equipments
        self.quality = quality
        self.basedefense = defense
        self.count = count

        self.Update()

    def __str__(self):
        pretty = '{0} [{1}] {2} pts\n\t'.format(self.name, self.count, self.cost)
        for w in self.equipments:
            pretty += str(w) + '\n\t'

        pretty += ', '.join(self.specialRules)
        pretty += '\n\t'
        pretty += 'Defense {0} pts, Attack {1} pts, Other {2} pts\n'.format(self.defenseCost, self.attackCost, self.otherCost)
        return pretty

    def __copy__(self):
        return Unit(self.name, self.count, self.quality, self.basedefense, self.equipments.copy(), self.specialRules.copy())

    @classmethod
    def from_dict(self, data, armory):
        return self(data['name'], data['count'], data['quality'], data['defense'], armory.get(data['equipment']), data['special'])

    def Update(self):
        self.wargearSp = [sp for equ in self.equipments for sp in equ.specialRules]
        self.parseSpecialRules()
        self.Cost()

    def AddEquipment(self, equipments):
        self.equipments += equipments
        self.Update()

    def RemoveEquipment(self, equipments):
        for e in equipments:
            self.equipments.remove(e)
        self.Update()

    def SetCount(self, count):
        self.count = count
        self.Cost()

    def AttackCost(self):
        self.attackCost = 0
        quality = self.quality
        if 'Good Shot' in self.specialRules + self.wargearSp:
            quality = 4
        for w in self.equipments + self.spEquipments:
            self.attackCost += w.Cost(self.speed, quality) * self.count

        self.attackCost = int(round(self.attackCost))

    def DefenseCost(self):
        self.defenseCost = quality_defense_factor(self.quality) * defense_cost(self.defense) * self.tough
        # include speed to defense cost. hardened target which move fast are critical to control objectives.
        self.defenseCost *= (self.speed + 24) / (36)
        self.defenseCost *= adjust_defense_cost * self.count
        self.defenseCost = int(round(self.defenseCost))

    # attack and defense cost should already be computed
    def OtherCost(self):
        self.otherCost = self.globalAdd
        self.otherCost += (self.attackCost + self.defenseCost) * self.globalMultiplier
        self.otherCost = int(round(self.otherCost))

    def Cost(self):
        self.DefenseCost()
        self.AttackCost()
        self.OtherCost()

        self.cost = self.defenseCost + self.attackCost + self.otherCost
        return self.cost

    def parseSpecialRules(self):
        self.speed = 12
        self.globalAdd = 0
        self.globalMultiplier = 0
        self.tough = 1
        self.defense = self.basedefense
        self.spEquipments = []

        specialRules = self.specialRules + self.wargearSp

        if 'Vehicle' in specialRules or 'Monster' in specialRules:
            smallStomp = Weapon('Monster Stomp', weaponRules=['Impact(3)'])
            self.spEquipments.append(smallStomp)
            if 'Fear' not in specialRules:
                specialRules.append('Fear')

        if 'Titan' in specialRules:
            titanStomp = Weapon('Titan Stomp', 0, 6, 2, ['Autohit'])
            self.spEquipments.append(titanStomp)
            if 'Fear' not in specialRules:
                specialRules.append('Fear')

        if 'Very Fast' in specialRules:
            self.speed = 24
        if 'Fast' in specialRules:
            self.speed = 18
        if 'Slow' in specialRules:
            self.speed = 8
        if 'Stealth' in specialRules:
            # Stealth is like +0.5 def, because it works only against ranged attack
            self.defense += 0.5

        if 'Ambush' in specialRules:
            if 'Scout' in specialRules:
                # Ambush and scout doesn't stack, since you can't use both
                self.globalMultiplier += 0.2
            else:
                self.globalMultiplier += 0.10
        if 'Scout' in specialRules:
            self.globalMultiplier += 0.15
        if 'Beacon' in specialRules:
            self.globalAdd += 10
        if 'Fear' in specialRules:
            self.globalAdd += 5
        if 'Strider' in specialRules:
            self.speed *= 1.2
        if 'Flying' in specialRules:
            self.speed *= 1.3
        # Flyers moves 36" but only in straight line.
        if 'Flyer' in specialRules:
            self.speed = 24

        for s in specialRules:
            if s.startswith('Tough'):
                self.tough = int(s[6:-1])
        if 'Regeneration' in specialRules:
            self.tough *= 4 / 3


def main():

    flamethrower = Weapon('Flamethrower', 12, 6, 0)
    flamethrower.Cost(12, 4)
    print(flamethrower.Pretty())

    gatling = Weapon('Gatling', 18, 4, 1)
    gatling.Cost(12, 4)
    print(gatling.Pretty())

    pulserifle = Weapon('Pulse Rifle', 30, 1, 1)
    pulserifle.Cost(12, 4)
    print(pulserifle.Pretty())

    plasma = Weapon('Plasma', 24, 1, 3, '')
    plasma.Cost(12, 4)
    print(plasma.Pretty())

    fusion = Weapon('Fusion Carbine', 18, 1, 7, ['Deadly'])
    fusion.Cost(12, 4)
    print(fusion.Pretty())

    railgun = Weapon('Railgun', 48, 1, 4, ['Linked', 'Deadly'])
    railgun.Cost(12, 4)
    print(railgun.Pretty())

    gundrone = WarGear('Gun Drone', ["Regeneration"], [pulserifle, railgun])
    print(gundrone)

    vehicle = Weapon('Vehicle', weaponRules=['Impact(3)'])
    vehicle.Cost(12, 4)
    print(vehicle)

    grunt = Unit('Grunt', 5, 5, 4, [pulserifle, gundrone], ['Good Shot'])
    print(grunt)

    grunt_cpt = Unit('Grunt_cpt', 1, 4, 4, [pulserifle], ['Tough(3)', 'Hero', 'Volley Fire'])
    print(grunt_cpt)

    suitfist = Weapon('Suit Fist', 0, 4, 1)
    battlesuit_cpt = Unit('Battlesuit Captain', 1, 3, 6, [suitfist], ['Ambush', 'Flying', 'Hero', 'Tough(3)'])
    print(battlesuit_cpt)


if __name__ == "__main__":
    # execute only if run as a script
    main()
