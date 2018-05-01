DEVICE_TYPE_DISPLAY equ 01h
DEVICE_TYPE_PRINTER equ 02h


FontFileHeader:
	.FileTag:       db 0FFh, "FONT   "
	                resq 1
	.PointerNumber: dw 1
	.PointerType:   db 1
	.InfoOffset:    dd FontInfoHeader
	
FontInfoHeader:
	.EntriesCount:  dw 2

	
ClavisBootUS437:
	._beginCodepageHeader:
	.CodeSize:      dw ._endCodepageHeader - ._beginCodepageHeader
	.Next:          dd ClavisBootCE852
	.DeviceType:    dw DEVICE_TYPE_DISPLAY
	.DeviceName:    db "EGA     "
	.Codepage:      incbin "../bin/clvsbtus.sys", 0, 2
	                resw 3
	.FontInfo:      dd ._beginDataHeader
	._endCodepageHeader:
	
	._beginDataHeader:
	                dw 1
	.FontsCount:    dw 1
	.FontsLength:   dw ._endFontData - ._beginFontData
	.CharacterRows: db 16
	.CharacterCols: db 8
	.AspectRatio:   resw 1
	.Characters:    dw 256
	._endDataHeader:
	
	._beginFontData:
	incbin "../bin/clvsbtus.sys", 2
	._endFontData:

	
ClavisBootCE852:
	._beginCodepageHeader:
	.CodeSize:      dw ._endCodepageHeader - ._beginCodepageHeader
	.Next:          dd Footer
	.DeviceType:    dw DEVICE_TYPE_DISPLAY
	.DeviceName:    db "EGA     "
	.Codepage:      incbin "../bin/clvsbtce.sys", 0, 2
	                resw 3
	.FontInfo:      dd ._beginDataHeader
	._endCodepageHeader:
	
	._beginDataHeader:
	                dw 1
	.FontsCount:    dw 1
	.FontsLength:   dw ._endFontData - ._beginFontData
	.CharacterRows: db 16
	.CharacterCols: db 8
	.AspectRatio:   resw 1
	.Characters:    dw 256
	._endDataHeader:
	
	._beginFontData:
	incbin "../bin/clvsbtce.sys", 2
	._endFontData:

Footer:
	db 0Dh, 0Ah
	db 'Celones(TM) Clavis EGA Font for DOS', 0Dh, 0Ah
	db '(C) 2018 Mateusz Karcz. All rights reserved.', 0Dh, 0Ah
	db 'Licensed according to the MIT License.'
	