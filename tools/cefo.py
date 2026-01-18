import io


class GlyphBlockBase:
    prefix: int
    offset: int

    def __init__(self) -> None:
        self.prefix = -1
        self.offset = -1


class FullGlyphBlock(GlyphBlockBase):
    size: int = 12

    widths: list[int]

    def __init__(self) -> None:
        super().__init__()
        self.widths = list()

    def load(self, data: bytes) -> None:
        offpfx = int.from_bytes(data[0:4], "little")
        widths = int.from_bytes(data[4:12], "little")

        self.prefix = offpfx & 0xFFF
        self.offset = offpfx >> 12
        self.widths = [(widths >> (i * 4)) & 0xF for i in range(16)]

    def store(self) -> bytes:
        offpfx = (self.offset << 12) | self.prefix
        widths = sum([self.widths[i] << (i * 4) for i in range(16)])

        data = offpfx.to_bytes(4, "little") + widths.to_bytes(8, "little")
        return data

    @classmethod
    def from_bytes(cls, data: bytes) -> 'FullGlyphBlock':
        block = cls()
        block.load(data)
        return block

    def __str__(self) -> str:
        return "<FullGlyphBlock {0:03X}0-{0:03X}F at {1:05X}>".format(self.prefix, self.offset)


class SparseGlyphBlock(GlyphBlockBase):
    size: int = 6

    widths: list[tuple[int, int]]

    def __init__(self) -> None:
        super().__init__()
        self.widths = list()

    def load(self, data: bytes, sgly: bytes) -> None:
        lenpfx = int.from_bytes(data[0:2], "little")
        offset = int.from_bytes(data[2:4], "little")
        sgly_offset = int.from_bytes(data[4:6], "little")
        sgly_data = sgly[sgly_offset:(sgly_offset + (lenpfx >> 12))]

        self.prefix = lenpfx & 0xFFF
        self.offset = offset
        self.widths = [(byte >> 4, byte & 0xF) for byte in sgly_data]

    def store(self, sgly_offset: int) -> tuple[bytes, bytes]:
        lenpfx = (len(self.widths) << 12) | self.prefix
        offset = self.offset

        data = lenpfx.to_bytes(2, "little") + offset.to_bytes(2, "little") + sgly_offset.to_bytes(2, "little")
        sgly_data = bytes(((i << 4) | w) for i, w in self.widths)
        return data, sgly_data

    @classmethod
    def from_bytes(cls, data: bytes, sgly: bytes) -> 'SparseGlyphBlock':
        block = cls()
        block.load(data, sgly)
        return block

    def __str__(self) -> str:
        return "<SparseGlyphBlock {} at {:05X}>".format(", ".join("{:03X}{:X}".format(self.prefix, i) for i, _ in self.widths), self.offset)


class CelonesFont:
    bitmap: bytes
    blocks: dict[int, FullGlyphBlock | SparseGlyphBlock]

    def __init__(self) -> None:
        self.bitmap = b""
        self.blocks = dict()

    def load(self, filename: str) -> None:
        with io.open(filename, mode="rb") as cefo:
            # Verify the basic header structure
            fourcc = cefo.read(4)
            if fourcc != b"RIFF":
                raise ValueError("File is not RIFF")

            size = int.from_bytes(cefo.read(4), "little")
            fourcc = cefo.read(4)
            if fourcc != b"CeFo":
                raise ValueError("File is not a Celones Font")

            # Load applicable RIFF chunks
            fblk, sblk, sgly, bmp = b"", b"", b"", b""
            while size > 0:
                fourcc = cefo.read(4)
                chunk_size = int.from_bytes(cefo.read(4), "little")
                data = cefo.read(chunk_size)

                if fourcc == b"fblk":
                    fblk = data
                elif fourcc == b"sblk":
                    sblk = data
                elif fourcc == b"sgly":
                    sgly = data
                elif fourcc == b"bmp ":
                    bmp = data

                size -= 8 + chunk_size

            # Populate full glyph block list
            count = round(len(fblk) / FullGlyphBlock.size)
            for i in range(count):
                block = FullGlyphBlock.from_bytes(fblk[i * FullGlyphBlock.size:])
                self.blocks[block.prefix] = block

            # Populate sparse glyph block list
            count = round(len(sblk) / SparseGlyphBlock.size)
            for i in range(count):
                block = SparseGlyphBlock.from_bytes(sblk[i * SparseGlyphBlock.size:], sgly)
                self.blocks[block.prefix] = block

            # Set the glyph bitmap
            self.bitmap = bmp

    def store(self, filename: str) -> None:
        with io.open(filename, mode="wb") as cefo:
            # Prepare full blocks
            fblk = bytearray()
            for _, block in self.blocks.items():
                if isinstance(block, FullGlyphBlock):
                    fblk.extend(block.store())

            # Prepare sparse blocks
            sblk = bytearray()
            sgly = bytearray()
            sparse_glyph_offset = 0
            for _, block in self.blocks.items():
                if isinstance(block, SparseGlyphBlock):
                    block_data, sgly_data = block.store(sparse_glyph_offset)
                    sblk.extend(block_data)
                    sgly.extend(sgly_data)
                    sparse_glyph_offset += len(sgly_data)

            # Prepare chunks
            if len(self.bitmap) % 2 != 0:
                self.bitmap += b"\0"

            chunks = [
                (b"fblk", fblk),
                (b"sblk", sblk),
                (b"sgly", sgly),
                (b"bmp ", self.bitmap)
            ]

            # Write the RIFF file
            cefo.write(b"RIFF")
            cefo.write((sum(len(data) + 8 for _, data in chunks) + 4).to_bytes(4, "little"))
            cefo.write(b"CeFo")

            for fourcc, data in chunks:
                cefo.write(fourcc)
                cefo.write(len(data).to_bytes(4, "little"))
                cefo.write(data)

    def __getitem__(self, index: int) -> bytes:
        prefix = index >> 4
        if prefix not in self.blocks:
            return b""

        block = self.blocks[prefix]

        if isinstance(block, FullGlyphBlock):
            start = block.offset + sum(block.widths[:index & 0xF])
            stop = start + block.widths[index & 0xF]
            return self.bitmap[start:stop]

        # Sparse block
        start = block.offset
        for i, width in block.widths:
            if i == index & 0xF:
                return self.bitmap[start:start + width]

            start += width

        return b""

    def print(self, text: str) -> bytearray:
        try:
            return bytearray(b"\0".join(self[ord(c)] for c in text))
        except MemoryError:
            return None # type: ignore
