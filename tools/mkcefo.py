import glob
import imageio.v3 as iio
import os.path
import re
import sys

from collections import defaultdict

from cefo import *


class GlyphSource:
    filename: str
    name: str
    size: int
    codepoints: list[int]

    pattern = re.compile(
        r"^(.+)(\d+)_([\da-fA-F]+(-[\da-fA-F]+)?(,[\da-fA-F]+(-[\da-fA-F]+)?)*)\.png$")

    def __init__(self, filename: str) -> None:
        m = re.match(self.pattern, os.path.basename(filename))
        if m is None:
            raise ValueError("File name '{}' is ill-formed".format(filename))

        self.filename = filename
        self.name = m[1]
        self.size = int(m[2])

        codepoints = list()
        for block in m[3].split(","):
            parts = block.split("-")
            start, stop = int(parts[0], base=16), int(parts[-1], base=16)
            if start > stop:
                raise ValueError("{} is not a valid block".format(block))

            for codepoint in range(start, stop + 1):
                codepoints.append(codepoint)

        self.codepoints = codepoints

    def __str__(self) -> str:
        return "{}: {} ({} px) - {} codepoints".format(self.filename, self.name, self.size, len(self.codepoints))

    def load(self) -> list[bytearray]:
        image = iio.imread(self.filename)
        if image.shape[0] != self.size:
            raise ValueError("Image height does not match the font size")

        glyphs = list()
        glyph = bytearray()
        for y in range(image.shape[1]):
            r, g, b = image[0][y][:3]
            if r == 255 and g == 0 and b == 0:
                glyphs.append(glyph)
                glyph = bytearray()
                continue

            scanline = 0
            for x in range(image.shape[0]):
                if image[x][y][0] == 0:
                    scanline = scanline + (1 << x)

            glyph.append(scanline)

        if len(glyphs) != len(self.codepoints):
            raise ValueError(
                "Image content does not match the number of codepoints")

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
    size: int
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

    def __init__(self, sources: list[GlyphSource]) -> None:
        self.name = sources[0].name
        self.size = sources[0].size
        groups = [zip(source.codepoints, source.load()) for source in sources]
        self.glyphs = list(sorted((Glyph(
            *pair) for group in groups for pair in group), key=lambda glyph: glyph.codepoint))

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


directory = sys.argv[1] if len(sys.argv) > 1 else "."
sources = [GlyphSource(file) for file in glob.glob(directory + "*.png")]
for source in sources:
    print(source)

font = BitmapFont(sources)

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
        cefo_block.widths = [(glyph.codepoint & 0xF, len(glyph)) for glyph in block.glyphs]

    cefo_block.prefix = block.prefix
    cefo.blocks[block.prefix] = cefo_block
    print(cefo_block)

cefo.store("{}{}.cefo".format(font.name, font.size))
