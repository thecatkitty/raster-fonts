import os.path

from argparse import ArgumentParser
from glob import glob
from itertools import groupby
from monobit import Font, Pack, load
from typing import Iterable, NamedTuple


# Font variant detection
class FontVariant(NamedTuple):
    format: str
    encoding: str


def get_variants_from_pack(pack: Pack, format: str) -> Iterable[FontVariant]:
    return (FontVariant(format, str(font.get_property("encoding"))) for font in pack)


def get_variants(yaff: str) -> Iterable[FontVariant]:
    prefix, _ = os.path.splitext(yaff)
    files = list(file for file in glob(prefix + ".*") if file != yaff)
    for file in files:
        _, ext = os.path.splitext(file)
        if ext == ".cefo":
            yield FontVariant(".cefo", "")

        else:
            for variant in get_variants_from_pack(load(file), ext):
                yield variant


# Pretty formatting variant info
def prettify_encoding(encoding: str) -> str:
    if encoding.startswith("cp"):
        return encoding.upper()

    if encoding.startswith("windows-"):
        return "CP" + encoding.removeprefix("windows-")

    return encoding


def prettify_format(format: str) -> str:
    return format[1:].upper()


def get_format_list(variants: Iterable[FontVariant]) -> Iterable[str]:
    for format, variants in groupby(variants, lambda v: v.format):
        encodings = ", ".join(sorted(prettify_encoding(variant.encoding)
                              for variant in variants
                              if len(variant.encoding) != 0))
        yield prettify_format(format if len(encodings) == 0 else f"{format} ({encodings})")


# Main script
parser = ArgumentParser(
    description="Utility for listing fonts in a directory",
    epilog="Copyright (c) Mateusz Karcz, 2026. Shared under the MIT License.")
parser.add_argument("dir", help="input font directory")
args = parser.parse_args()

for yaff in sorted(glob(os.path.join(args.dir, "*.yaff"))):
    font: Font = load(yaff).get(0)
    formats = sorted(["YAFF"] + sorted(get_format_list(get_variants(yaff))))
    print(f"- {font.family} - {', '.join(formats)}")
