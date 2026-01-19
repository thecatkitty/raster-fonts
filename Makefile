SIL ?= @

CEFO  = python3 tools/yaff2cefo.py
CONV  = monobit-convert
MKDIR = mkdir -p


all: clavis clavis-bold gidotto

clean:
	@rm -rf out


font_target = $1: $(addprefix out/$1,.yaff $2)

$(call font_target,clavis,.bdf .cpi)
$(call font_target,clavis-bold,.bdf .cpi)
$(call font_target,gidotto,.bdf .cefo)


out/%.bdf: out/%.yaff | out/.
	@echo "CONV  $(@F)"
	$(SIL)$(CONV) $< to $@ -overwrite

out/%.cefo: out/%.yaff | out/.
	@echo "CEFO  $(@F)"
	$(SIL)$(CEFO) $< $@

out/%.cpi: out/%.yaff | out/.
	@echo "CONV  $(@F)"
	$(SIL)$(CONV) $< to $@ -overwrite `cat $(basename $(@F))/cpi.args`


out/%.yaff: %/head.yaff $(sort %/*-*.yaff) | out/.
	@echo "BUILD $(@F)"
	$(SIL)cat $^ > $@


.PRECIOUS: out/.

%/.:
	@echo "MKDIR $(@D)"
	$(SIL)$(MKDIR) $(@D)
