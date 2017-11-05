FACTIONS = Battle_Brothers Tao Robot_Legions High_Elf_Fleets

TEX := $(foreach d,$(FACTIONS),$(wildcard $(d)/*.tex))
TEMPLATE := $(wildcard template/*.sty)
PDF := $(TEX:.tex=.pdf)
OUT_PDF := $(addprefix out/,$(notdir $(PDF)))
PYTHONS := $(wildcard *.py)
COMMON := $(wildcard Common/*.json)

CLEAN := $(foreach d,$(FACTIONS),$(wildcard $(d)/*.csv) $(wildcard $(d)/*.pdf))

# $(1) is Faction, $(2) is Faction/*.json
# so Faction/Faction.pdf will depend on all Faction/*.json
# and Faction will depend on out/Faction.pdf
define add_dep =
$(1)/$(1).pdf: $(2)

.PHONY : $(1)
$(1): out/$(1).pdf
endef

define copy_out =
$(1): $(2)
	@cp $$< $$@
endef

all: $(OUT_PDF)

.PHONY: clean
clean:
	@echo Removing $(CLEAN)
	@rm -f $(CLEAN)
	@rm -rf out

indent:
	@python3 indentjson.py $(FACTIONS) Common

out:
	@mkdir out

# pdf dependency is the tex file, all faction json files, all python scripts, and latex templates
%.pdf : %.tex $(PYTHONS) $(COMMON) $(TEMPLATE) | out
	@rm -f $(@D)/*.csv
	@python3 onepagebatch.py $(@D)
	@ echo Generating $@
	@cd $(@D) && xelatex -interaction=batchmode -halt-on-error $(notdir $<) 2>&1 > /dev/null

# copy all pdf to out/ directory
$(foreach f,$(PDF),$(eval $(call copy_out,$(addprefix out/,$(notdir $(f))),$(f))))

# add dependency to all json found in faction directory
$(foreach d,$(FACTIONS),$(eval $(call add_dep,$(d),$(wildcard $(d)/*.json))))
