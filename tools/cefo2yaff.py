from argparse import ArgumentParser
from cefo import CelonesFont, FullGlyphBlock, GlyphBlockBase, SparseGlyphBlock
from monobit import Glyph, Font, storage
from os.path import basename, splitext
from typing import Generator


def get_glyph_data(block: GlyphBlockBase) -> Generator[tuple[int, bytes], None, None]:
    if isinstance(block, FullGlyphBlock):
        for i in range(16):
            width = block.widths[i]
            offset = block.offset + sum(block.widths[:i])
            yield (block.prefix << 4) + i, cefo.bitmap[offset:offset + width]

    elif isinstance(block, SparseGlyphBlock):
        for i, width in block.widths:
            offset = block.offset + sum(w for _, w in block.widths if _ < i)
            yield (block.prefix << 4) + i, cefo.bitmap[offset:offset + width]


def get_scanline(data: bytes, line: int) -> str:
    mask = 1 << line
    return "".join("1" if column & mask else "0" for column in data)


def get_raster(data: bytes) -> tuple:
    return tuple(get_scanline(data, line) for line in range(8))


def get_glyph(codepoint: int, raster: tuple) -> Glyph:
    return Glyph(pixels=raster, char=chr(codepoint))


parser = ArgumentParser(
    description="Utility for converting Celones Font files to YAFF format",
    epilog="Copyright (c) Mateusz Karcz, 2026. Shared under the MIT License.")
parser.add_argument("input", help="input Celones Font file")
parser.add_argument("output", help="output YAFF file")
args = parser.parse_args()

cefo = CelonesFont()
cefo.load(args.input)

glyphs = list()

for _, block in cefo.blocks.items():
    for codepoint, data in get_glyph_data(block):
        glyphs.append(get_glyph(codepoint, get_raster(data)))

yaff = Font(tuple(glyphs))
yaff.name = splitext(basename(args.input))[0]
storage.save(yaff, args.output, format="yaff", overwrite=True)
