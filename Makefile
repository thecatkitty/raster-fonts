all: clavis clavis-bold

clean:
	rm -rf out


clavis: \
	out/clavis.yaff \
	out/clavis.cpi

clavis-bold: \
	out/clavis-bold.yaff \
	out/clavis-bold.cpi


out/%.cpi: out/%.yaff
	@mkdir -p $(@D)
	monobit-convert $< to $@ `cat $(basename $(notdir $@))/cpi.args`

out/%.yaff: %/head.yaff %/*-*.yaff
	@mkdir -p $(@D)
	cat $^ > $@
