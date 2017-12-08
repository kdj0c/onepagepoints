# onepagepoints
small python 3.7 script to calculate units points for onepagerule Grimdark Future

It needs some tweaks. compared to onepagerule points, this algorithm lower the weapon cost, and increase the cost of high defense, high toughness units.

# Install

Tested only with python 3.7 on Archlinux. It should work everywhere you can run python/Latex

# Dependencies :

To generate the pdf, you need xelatex, with a few plugins. csvsimple is not needed anymore.
The best is to install from ctan at https://www.tug.org/texlive/quickinstall.html)
You also need make, to build everything

# Files details

 * onepagepoints.py : library to calculate individual cost of weapons/units, also a main() to do unit tests
 * onepagebatch.py : script which read each faction .yml files (equipments.yml, faction.yml, units.yml, upgrades.yml), and generate .html, .tex, and .txt output.
 * indentyaml.py : script to indent and force format for all .yml files.
 * generate_faction.py : script that is only used once to create a new faction
 * testpoints.py : a small pytest script, I didn't put much unit test here. It can be used to check for regression.
 * Template/header.html : html/css header to generate a cool html page.
 * Template/header.tex : LaTeX header file, which define all LaTeX macros which will be used to generate the pdf.
 * Makefile : simple script to generate all pdf at once !
 * Faction/Faction.ods : source file used by generate_faction.py. it's used only once, I keep them here only for example.

# commands :

to build all factions pdf (they are generated in out/Faction.pdf):
$ `make -j4`

to build only 'Tao' pdf :
$ `make Tao`

to indent all yaml files :
$ `make indent`

# Tricks

Sometime xelatex fails randomly. it occurs when it doesn't have enough RAM. I have 4G RAM without swap, and if I have too much tabs in Firefox, xelatex will fail with random error.
