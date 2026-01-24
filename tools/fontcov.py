import importlib
import monobit
import sys
import unicodedata

from argparse import ArgumentParser
from collections import Counter
from typing import Iterable
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


def get_codepage_counts(glyphs: Iterable[monobit.Glyph], codepage: int) -> tuple[int, int]:
    encoding = importlib.import_module(f"encodings.cp{codepage}")
    table = patch_ibm_codepage(
        encoding.decoding_table) if codepage in IBMGRAPH_CODEPAGES else encoding.decoding_table
    total = len(set(filter(is_printable, (ord(char) for char in table))))
    count = sum(chr(cp) in table for cp in codepoints_from_glyphs(glyphs))
    return count, total


# Coverage statistics
def get_block_coverage(glyphs: Iterable[monobit.Glyph]) -> Iterable[tuple[str, int, int]]:
    unicode_blocks = get_block_counts(range(sys.maxunicode + 1))
    for block, count in get_block_counts(codepoints_from_glyphs(glyphs)).items():
        yield block, count, unicode_blocks[block]


def get_codepage_coverage(glyphs: Iterable[monobit.Glyph], codepages: list[int]) -> Iterable[tuple[str, int, int]]:
    for number in codepages:
        count, total = get_codepage_counts(glyphs, number)
        yield f"CP{number}", count, total


# Main script
parser = ArgumentParser(
    description="Utility for measuring font charset coverage",
    epilog="Copyright (c) Mateusz Karcz, 2026. Shared under the MIT License.")
parser.add_argument("input", help="input font file")
parser.add_argument("--cp", type=int, nargs="*", default=list(),
                    help="code pages to measure against (none for Unicode block coverage)")
parser.add_argument("--md", action="store_true",
                    help="output as Markdown table")
args = parser.parse_args()

pack: monobit.Pack = monobit.load(args.input)
font: monobit.Font = pack.get(0)

report = list(get_block_coverage(font.glyphs) if len(args.cp) ==
              0 else get_codepage_coverage(font.glyphs, args.cp))
width = max(len(block) for block, _, _ in report)

if args.md:
    column_title = "Unicode block" if len(args.cp) == 0 else "Character set"
    width = max(width, len(column_title))
    print(f"| {column_title:{width}s} | {'Coverage':>19s} |")
    print("| " + (width * "-") + " | " + (19 * "-") + " |")

    for block, count, total in report:
        coverage = f"{100 * count / total:.1f}% ({count}/{total})"
        print(f"| {block:{width}s} | {coverage:>19s} |")

else:
    for block, count, total in report:
        print(f"{block:{width}s}  {count:5d}/{total:<5d}  {100 * count / total:5.1f}%")
