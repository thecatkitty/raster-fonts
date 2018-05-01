# Raster fonts for EGA text mode
Clavis Boot/Clavis EGA font created initially for my own operating system project. Currently it supports only `437` (US-ASCII) and `852` (DOS-Central Europe) code pages.

* `clvsbtus.sys` - Clavis Boot US (CP437)
* `clvsbtce.sys` - Clavis Boot CE (CP852)
* `claviseg.cpi` - Clavis EGA Font for DOS (CP437, CP852)

## Building
To build SYS and CPI files the Netwide Assembler (NASM) is needed.

```nasm -f bin -o bin/<destination> src/<source>```
  
__To build the CPI file You need to build SYS files first!__

## SYS file structure (for use in Your OS)
```
     2B  Code page number (little endian)
256*16B  Glyphs
```

Each glyph is 8 pixels wide and 16 pixels high. The most significant bit of the first byte is the top-left corner, while the least significant bit of the last byte is the bottom-right corner.

## Installation in MS-DOS
Copy `claviseg.cpi` to the DOS files path (`C:\DOS` in this example) and then add these lines to `autoexec.bat`:

```
mode con codepage prepare=((<code page>) C:\DOS\CLAVISEG.CPI)
mode con codepage select=<code page>
````

Remember that currently only 437 and 852 code pages are supported!
