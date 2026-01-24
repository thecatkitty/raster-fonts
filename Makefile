SIL ?= @

CEFO  = python3 tools/yaff2cefo.py
CONV  = monobit-convert
CVRGE = python3 tools/fontcov.py
MKDIR = mkdir -p

FONTS = clavis clavis-bold gidotto


.PHONY: all clean $(FONTS) coverage

all: $(FONTS) coverage

clean:
	@rm -rf int out

coverage: out/coverage.md


font_target = $1: $(addprefix out/$1,.yaff $2)

$(call font_target,clavis,.bdf .cpi .1250.fon .1252.fon)
$(call font_target,clavis-bold,.bdf .cpi .1250.fon)
$(call font_target,gidotto,.bdf .cefo .1250.fon)


out/%.bdf: out/%.yaff | out/.
	@echo "CONV  $(@F)"
	$(SIL)$(CONV) $< to $@ -overwrite

out/%.cefo: out/%.yaff | out/.
	@echo "CEFO  $(@F)"
	$(SIL)$(CEFO) $< $@

out/%.cpi: out/%.yaff | out/.
	@echo "CONV  $(@F)"
	$(SIL)$(CONV) $< to $@ -overwrite `cat $(basename $(@F))/cpi.args`

out/%.fon: int/%.yaff | out/.
	@echo "CONV  $(@F)"
	$(SIL)$(CONV) $< to $@ -overwrite -format=mzfon


out/coverage.md: $(addprefix out/$1,$(addsuffix .yaff,$(FONTS)))
	@echo "CVRGE $(@F)"
	$(SIL)echo "## Unicode coverage" > $@
	$(SIL)$(CVRGE) $^ --md >> $@
	$(SIL)echo >> $@
	$(SIL)echo "## Code page coverage" >> $@
	$(SIL)$(CVRGE) $^ --cp 437 852 1250 1252 --md >> $@


define subcp_target
int/%.$1.yaff: out/%.yaff | int/.
	@echo "SUBCP $$(@F)"
	$(SIL)$(CONV) $$< resample -encoding=cp$1 | sed -r "/^family:/ s/$$$$/ $2/" > $$@
endef

.SECONDARY:
$(eval $(call subcp_target,1250,CE))
$(eval $(call subcp_target,1252,Western))

out/%.yaff: %/head.yaff $(sort %/*-*.yaff) | out/.
	@echo "BUILD $(@F)"
	$(SIL)cat $^ > $@


.PRECIOUS: int/. out/.

%/.:
	@echo "MKDIR $(@D)"
	$(SIL)$(MKDIR) $(@D)
