# SPDX-License-Identifier: BSD-3-Clause
from enum import Enum, unique

__all__ = ('Opcodes', 'ALUOpcode', 'LogicOpcode', 'BitOpcode')

@unique
class Opcodes(Enum):
	NOP    = 0
	RETURN = 1
	RETFIE = 2
	SLEEP  = 3
	#CLRWDT = 4
	MOVWF  = 5
	CLRW   = 6
	CLRF   = 7
	SUBWF  = 8
	DECF   = 9
	IORWF  = 10
	ANDWF  = 11
	XORWF  = 12
	ADDWF  = 13
	MOVF   = 14
	COMF   = 15
	INCF   = 16
	DECFSZ = 17
	RRF    = 18
	RLF    = 19
	SWAPF  = 20
	INCFSZ = 21
	BCF    = 22
	BSF    = 23
	BTFSC  = 24
	BTFSS  = 25
	CALL   = 26
	GOTO   = 27
	MOVLW  = 28
	RETLW  = 29
	IORLW  = 30
	ANDLW  = 31
	XORLW  = 32
	SUBLW  = 33
	ADDLW  = 34

@unique
class ArithOpcode(Enum):
	ADD = 1
	SUB = 2
	INC = 3
	DEC = 4

@unique
class LogicOpcode(Enum):
	NONE = 0
	AND = 1
	OR = 2
	XOR = 3

@unique
class BitOpcode(Enum):
	NONE = 0
	ROTR = 1
	ROTL = 2
	SWAP = 3
	BITCLR = 4
	BITSET = 5
