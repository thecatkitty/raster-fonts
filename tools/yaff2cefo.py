import monobit

from argparse import ArgumentParser
from collections import defaultdict

from cefo import *


class GlyphSource:
    filename: str
    font: monobit.Font

    def __init__(self, filename: str) -> None:
        self.filename = filename
        pack: monobit.Pack = monobit.load(self.filename)
        self.font = pack.get(0)

    def __str__(self) -> str:
        return f"{self.filename}: {self.font.name} - {len(self.font.glyphs)} glyphs"

    def load(self) -> list[tuple[int, bytearray]]:
        glyphs = list()

        for glyph in self.font.glyphs:
            assert isinstance(glyph, monobit.Glyph)

            codepoint = ord(glyph.char)
            bitmap = bytearray()

            pixels = glyph.as_matrix()
            for column in range(glyph.width):
                scanline = 0
                for row in range(glyph.height):
                    if pixels[row][column] != 0:
                        scanline |= 1 << row

                bitmap.append(scanline)

            glyphs.append((codepoint, bitmap))

        return glyphs


class Glyph:
    codepoint: int
    bitmap: bytearray

    def __init__(self, codepoint: int, bitmap: bytearray) -> None:
        self.codepoint = codepoint
        self.bitmap = bitmap

    def __len__(self) -> int:
        return len(self.bitmap)


class GlyphBlock:
    prefix: int
    glyphs: list[Glyph]

    def __init__(self, glyphs: list[Glyph]) -> None:
        self.prefix = glyphs[0].codepoint >> 4
        self.glyphs = glyphs

    def __len__(self) -> int:
        return len(self.glyphs)


class BitmapFont:
    name: str
    glyphs: list[Glyph]

    class _Iterator:
        _i: int
        _font: 'BitmapFont'

        def __init__(self, font: 'BitmapFont') -> None:
            self._i = 0
            self._font = font

        def __next__(self) -> Glyph:
            if self._i >= len(self._font.glyphs):
                raise StopIteration

            result = self._font.glyphs[self._i]
            self._i += 1
            return result

    def __init__(self, source: GlyphSource) -> None:
        self.name = source.font.name
        self.glyphs = list(sorted(
            (Glyph(*pair) for pair in source.load()), key=lambda glyph: glyph.codepoint))

    def __iter__(self):
        return BitmapFont._Iterator(self)

    def get_offset(self, codepoint: int):
        return sum(len(glyph) for glyph in self.glyphs[:next(i for i, v in enumerate(self.glyphs) if v.codepoint == codepoint)])

    def get_blocks(self) -> list[GlyphBlock]:
        blocks = defaultdict(list)
        for glyph in font:
            blocks[glyph.codepoint >> 4].append(glyph)

        return [GlyphBlock(v) for v in blocks.values()]

    def to_bitmap(self) -> bytearray:
        result = bytearray()
        for glyph in self.glyphs:
            result.extend(glyph.bitmap)

        return result


parser = ArgumentParser(
    description="Utility for converting YAFF files to Celones Font format",
    epilog="Copyright (c) Mateusz Karcz, 2022-2026. Shared under the MIT License.")
parser.add_argument("input", help="input YAFF file")
parser.add_argument("output", help="output Celones Font file")
args = parser.parse_args()

source = GlyphSource(args.input)
print(source)

font = BitmapFont(source)

cefo = CelonesFont()
cefo.bitmap = font.to_bitmap()

for block in font.get_blocks():
    cefo_block: GlyphBlockBase
    if len(block) == 16:
        cefo_block = FullGlyphBlock()
        cefo_block.offset = font.get_offset(block.prefix << 4)
        cefo_block.widths = [len(glyph) for glyph in block.glyphs]
    else:
        cefo_block = SparseGlyphBlock()
        cefo_block.offset = font.get_offset(
            (block.prefix << 4) | (block.glyphs[0].codepoint & 0xF))
        cefo_block.widths = [(glyph.codepoint & 0xF, len(glyph))
                             for glyph in block.glyphs]

    cefo_block.prefix = block.prefix
    cefo.blocks[block.prefix] = cefo_block
    print(cefo_block)

cefo.store(args.output)
