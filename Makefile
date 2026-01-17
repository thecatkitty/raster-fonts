all: clavis

clean:
	rm -rf out


clavis: \
	out/clavis.yaff \
	out/clavis.cpi


out/%.cpi: out/%.yaff
	@mkdir -p $(@D)
	monobit-convert $< to $@ `cat $(basename $(notdir $@))/cpi.args`

out/%.yaff: %/head.yaff %/*-*.yaff
	@mkdir -p $(@D)
	cat $^ > $@
