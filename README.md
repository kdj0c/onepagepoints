# onepagepoints
small python 3.7 script to calculate units points for onepagerule Grimdark Future

It needs some tweaks. compared to onepagerule points, this algorithm lower the weapon cost, and increase the cost of high defense, high toughness units.

# Install

Tested only with python 3.7 on Archlinux. It should work everywhere you can run python/Latex

# Dependencies :

To generate the pdf, you need xelatex, with a few plugins, a recent version of csvsimple (1.12 is too old, 1.20 works), If you get an error about "I do not know the key '/csv/filter strcmp'", then you need a newer csvsimple.
The best is to install from ctan at https://www.tug.org/texlive/quickinstall.html)
You also need make, to build everything

If you want to create a new faction, you need also pyexcel-ods3 (you can install it with "sudo pip install pyexcel-ods3")

# Files details

 * onepagepoints.py : library to calculate individual cost of weapons/units, also a main() to do unit tests
 * onepagebatch.py : script which read each faction .json files (equipments.json, units.json, upgrades.json), and generate units.csv and upgrades.csv which will be integrated into Latex to generate the pdf table.
 * indentjson.py : script to indent and force format for all .json files.
 * generate_faction.py : script that is only used once to create a new faction
 * testpoints.py : a small pytest script, I didn't put much unit test here. It can be used to check for regression.
 * Template/grimdark.sty : latex template to generate beautiful tables, and avoid to much duplication in all Faction.tex
 * Faction/Faction.tex : latex source file for the Faction
 * Makefile : simple script to generate all pdf at once !
 * Faction/Faction.ods : source file used by generate_faction.py. it's used only once, I keep them here only for example.

# commands :

to build all factions pdf (they are generated in out/Faction.pdf):
$ `make`

to build only 'Tao' pdf :
$ `make Tao`

to indent all json files :
$ `make indent`

# Tricks

Sometime xelatex fails randomly. it occurs when it doesn't have enough RAM. I have 4G RAM without swap, and if I have too much tabs in Firefox, xelatex will fail with random error.
