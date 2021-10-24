from enum import IntEnum, unique

__all__ = (
	'SPIOpcodes',
	'QSPIOpcodes',
)

@unique
class SPIOpcodes(IntEnum):
	enableQSPI = 0x38

@unique
class QSPIOpcodes(IntEnum):
	writeEnable = 0x06
	writeEnableVolatile = 0x50
	fastRead = 0x0B
	pageProgram = 0x02
	blockErase4k = 0x20
	blockErase32k = 0x52
	blockErase64k = 0xD8
	chipErase = 0xC7
	readDID = 0x90
	readJEDEC = 0x9F
	fastReadQIO = 0xEB
