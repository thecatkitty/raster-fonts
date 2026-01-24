import importlib
import monobit
import sys
import unicodedata

from argparse import ArgumentParser
from collections import Counter
from typing import Iterable, NamedTuple
from unidata_blocks import get_block_by_code_point


# IBM PC memory-mapped video graphics
# See: https://www.unicode.org/Public/MAPPINGS/VENDORS/MISC/IBMGRAPH.TXT
# and: https://www.unicode.org/Public/MAPPINGS/VENDORS/MICSFT/PC/
def patch_ibm_codepage(table: str) -> str:
    IBMGRAPH = (
        '\u0000'  # NUL
        '\u263A'  # WHITE SMILING FACE
        '\u263B'  # BLACK SMILING FACE
        '\u2665'  # BLACK HEART SUIT
        '\u2666'  # BLACK DIAMOND SUIT
        '\u2663'  # BLACK CLUB SUIT
        '\u2660'  # BLACK SPADE SUIT
        '\u2022'  # BULLET
        '\u25D8'  # INVERSE BULLET
        '\u25CB'  # WHITE CIRCLE
        '\u25D9'  # INVERSE WHITE CIRCLE
        '\u2642'  # MALE SIGN
        '\u2640'  # FEMALE SIGN
        '\u266A'  # EIGHTH NOTE
        '\u266B'  # BEAMED EIGHTH NOTES
        '\u263C'  # WHITE SUN WITH RAYS
        '\u25BA'  # BLACK RIGHT-POINTING POINTER
        '\u25C4'  # BLACK LEFT-POINTING POINTER
        '\u2195'  # UP DOWN ARROW
        '\u203C'  # DOUBLE EXCLAMATION MARK
        '\u00B6'  # PILCROW SIGN
        '\u00A7'  # SECTION SIGN
        '\u25AC'  # BLACK RECTANGLE
        '\u21A8'  # UP DOWN ARROW WITH BASE
        '\u2191'  # UPWARDS ARROW
        '\u2193'  # DOWNWARDS ARROW
        '\u2192'  # RIGHTWARDS ARROW
        '\u2190'  # LEFTWARDS ARROW
        '\u221F'  # RIGHT ANGLE
        '\u2194'  # LEFT RIGHT ARROW
        '\u25B2'  # BLACK UP-POINTING TRIANGLE
        '\u25BC'  # BLACK DOWN-POINTING TRIANGLE
    )
    return IBMGRAPH + table[len(IBMGRAPH):]


IBMGRAPH_CODEPAGES = [437, 737, 775, 850, 852, 855,
                      857, 860, 861, 862, 863, 865, 866, 869, 874]


# Charset population aggregates
def is_printable(cp) -> bool:
    return not unicodedata.category(chr(cp)).startswith("C")


def codepoints_from_glyphs(glyphs: Iterable[monobit.Glyph]) -> Iterable[int]:
    return sorted(set(filter(is_printable, (ord(char)
                                            for glyph in glyphs
                                            for char in glyph.chars))))


def get_block_counts(codepoints: Iterable[int]) -> Counter[str]:
    return Counter(cp.name
                   for cp in map(get_block_by_code_point, filter(is_printable, codepoints))
                   if cp is not None)


def get_codepoint_table(codepage: int) -> str:
    encoding = importlib.import_module(f"encodings.cp{codepage}")
    return patch_ibm_codepage(encoding.decoding_table) if codepage in IBMGRAPH_CODEPAGES else encoding.decoding_table


def get_codepage_count(glyphs: Iterable[monobit.Glyph], codepage: int) -> int:
    table = get_codepoint_table(codepage)
    count = sum(chr(cp) in table for cp in codepoints_from_glyphs(glyphs))
    return count


def get_codepage_total(codepage: int) -> int:
    table = get_codepoint_table(codepage)
    total = len(set(filter(is_printable, (ord(char) for char in table))))
    return total


# Coverage statistics
class CoverageReport(NamedTuple):
    block: str
    counts: list[int]
    total: int


def get_block_coverage(glyph_sets: Iterable[Iterable[monobit.Glyph]]) -> Iterable[CoverageReport]:
    unicode_blocks = get_block_counts(range(sys.maxunicode + 1))
    glyph_set_counts = list(
        map(get_block_counts, map(codepoints_from_glyphs, glyph_sets)))

    for block, count in unicode_blocks.items():
        counts = list(glyph_set_count[block]
                      if block in glyph_set_count else 0
                      for glyph_set_count in glyph_set_counts)
        if sum(counts) > 0:
            yield CoverageReport(block, counts, count)


def get_codepage_coverage(glyph_sets: Iterable[Iterable[monobit.Glyph]], codepages: list[int]) -> Iterable[CoverageReport]:
    for number in codepages:
        total = get_codepage_total(number)
        counts = [get_codepage_count(glyphs, number) for glyphs in glyph_sets]
        yield CoverageReport(f"CP{number}", counts, total)


# Main script
parser = ArgumentParser(
    description="Utility for measuring font charset coverage",
    epilog="Copyright (c) Mateusz Karcz, 2026. Shared under the MIT License.")
parser.add_argument("input", nargs="*", help="input font files")
parser.add_argument("--cp", type=int, nargs="*", default=list(),
                    help="code pages to measure against (none for Unicode block coverage)")
parser.add_argument("--md", action="store_true",
                    help="output as Markdown table")
args = parser.parse_args()

packs = map(monobit.load, args.input)
fonts: list[monobit.Font] = list(map(lambda pack: pack.get(0), packs))
glyph_sets = list(map(lambda font: font.glyphs, fonts))

report = list(get_block_coverage(glyph_sets) if len(args.cp) ==
              0 else get_codepage_coverage(glyph_sets, args.cp))
width = max(len(block) for block, _, _ in report)

if args.md:
    first_title = "Unicode block" if len(args.cp) == 0 else "Character set"
    first_width = max(width, len(first_title))
    titles = ["Coverage"] if len(fonts) == 1 else [
        font.family for font in fonts]
    widths = list(map(len, titles))

    print(f"| {first_title:{width}s} |", end="")
    for title, width in zip(titles, widths):
        print(f" {title:>{max(19, width)}s} |", end="")
    print()

    print("| " + (first_width * "-") + " |", end="")
    for width in widths:
        print(" " + (max(19, width) * "-") + " |", end="")
    print()

    for block, counts, total in report:
        print(f"| {block:{first_width}s} |", end="")
        for count in counts:
            coverage = "-" if count == 0 else f"{100 * count / total:.1f}% ({count}/{total})"
            print(f" {coverage:>19s} |", end="")
        print()

else:
    for i, font in enumerate(fonts):
        print(font.family)
        for block, counts, total in report:
            if counts[i] > 0:
                print(
                    f"\t{block:{width}s}  {counts[i]:5d}/{total:<5d}  {100 * counts[i] / total:5.1f}%")
        print()
