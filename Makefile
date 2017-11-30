# for reproducible build
SOURCE_DATE_EPOCH := 0
export SOURCE_DATE_EPOCH

FACTIONS := Battle_Brothers Tao Robot_Legions High_Elf_Fleets Orc
# Output directory
OUT := build

PDF := $(addprefix $(OUT)/,$(addsuffix .pdf,$(FACTIONS)))
PYTHONS := $(wildcard *.py)
COMMON := $(wildcard Common/*.yml)

TEX_TEMPLATE := $(wildcard Template/*.tex)
HTML_TEMPLATE := $(wildcard Template/*.html)

TEX_TEMPDIR := $(OUT)/tex
TXT_TEMPDIR := $(OUT)/txt

# don't use built-in rules
.SUFFIXES:

# $(1) is Faction, $(2) is Faction/*.yml
# so out/Faction.pdf will depend on Faction/*.yml *.py Common/*.yml template/*.tex
# and Faction will depend on out/Faction.pdf
define build_pdf =
$(OUT)/$(1).pdf: $(2) $(PYTHONS) $(COMMON) $(TEX_TEMPLATE) $(HTML_TEMPLATE) | $(TEX_TEMPDIR)
	@python3 onepagebatch.py -b $(OUT) $(1)
	@echo Generating $$@
	@cd $(TEX_TEMPDIR) && xelatex -interaction=batchmode -halt-on-error $(1).tex 2>&1 > /dev/null
	@mv $(TEX_TEMPDIR)/$(1).pdf $$@

# Handy alias to build a faction, "make Tao" will do "make build/Tao.pdf"
.PHONY : $(1)
$(1): $(OUT)/$(1).pdf
endef

all: $(PDF)

.PHONY: clean
clean:
	@echo Removing `find $(OUT)`
	@rm -rf $(OUT)

.PHONY: indent
indent:
	@python3 indentyaml.py $(FACTIONS) Common

$(OUT):
	@mkdir -p $@

$(TEX_TEMPDIR):
	@mkdir -p $@

$(TXT_TEMPDIR):
	@mkdir -p $@

# rules to build a pdf for each faction
$(foreach d,$(FACTIONS),$(eval $(call build_pdf,$(d),$(wildcard $(d)/*.yml))))
