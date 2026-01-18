all: clavis clavis-bold gidotto

clean:
	rm -rf out


clavis: \
	out/clavis.yaff \
	out/clavis.cpi

clavis-bold: \
	out/clavis-bold.yaff \
	out/clavis-bold.cpi

gidotto: \
	out/gidotto.yaff \
	out/gidotto.cefo


out/%.cefo: out/%.yaff
	@mkdir -p $(@D)
	python3 tools/yaff2cefo.py $< $@

out/%.cpi: out/%.yaff
	@mkdir -p $(@D)
	monobit-convert $< to $@ `cat $(basename $(notdir $@))/cpi.args`

out/%.yaff: %/head.yaff %/*-*.yaff
	@mkdir -p $(@D)
	cat $^ > $@
