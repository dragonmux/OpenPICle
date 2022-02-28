# SPDX-License-Identifier: BSD-3-Clause
from amaranth import Elaboratable, Module, Signal
from .types import Opcodes

__all__ = ["Decoder"]

class Decoder(Elaboratable):
	def __init__(self):
		self.instruction = Signal(14)
		self.opcode = Signal(Opcodes)

	def elaborate(self, platform):
		m = Module()

		with m.Switch(self.instruction):
			with m.Case('00 0000 0--0 0000'):
				m.d.comb += self.opcode.eq(Opcodes.NOP)
			with m.Case('00 0000 0000 1000'):
				m.d.comb += self.opcode.eq(Opcodes.RETURN)
			with m.Case('00 0000 0000 1001'):
				m.d.comb += self.opcode.eq(Opcodes.RETFIE)
			with m.Case('00 0000 0110 0011'):
				m.d.comb += self.opcode.eq(Opcodes.SLEEP)
			# CLRWDT is skipped here as we don't have a WDT.
			with m.Case('00 0000 1--- ----'):
				m.d.comb += self.opcode.eq(Opcodes.MOVWF)
			with m.Case('00 0001 0--- ----'):
				m.d.comb += self.opcode.eq(Opcodes.CLRW)
			with m.Case('00 0001 1--- ----'):
				m.d.comb += self.opcode.eq(Opcodes.CLRF)
			with m.Case('00 0010 ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.SUBWF)
			with m.Case('00 0011 ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.DECF)
			with m.Case('00 0100 ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.IORWF)
			with m.Case('00 0101 ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.ANDWF)
			with m.Case('00 0110 ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.XORWF)
			with m.Case('00 0111 ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.ADDWF)
			with m.Case('00 1000 ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.MOVF)
			with m.Case('00 1001 ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.COMF)
			with m.Case('00 1010 ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.INCF)
			with m.Case('00 1011 ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.DECFSZ)
			with m.Case('00 1100 ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.RRF)
			with m.Case('00 1101 ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.RLF)
			with m.Case('00 1110 ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.SWAPF)
			with m.Case('00 1111 ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.INCFSZ)
			with m.Case('01 00-- ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.BCF)
			with m.Case('01 01-- ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.BSF)
			with m.Case('01 10-- ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.BTFSC)
			with m.Case('01 11-- ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.BTFSS)
			with m.Case('10 0--- ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.CALL)
			with m.Case('10 1--- ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.GOTO)
			with m.Case('11 00-- ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.MOVLW)
			with m.Case('11 01-- ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.RETLW)
			with m.Case('11 1000 ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.IORLW)
			with m.Case('11 1001 ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.ANDLW)
			with m.Case('11 1010 ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.XORLW)
			with m.Case('11 110- ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.SUBLW)
			with m.Case('11 111- ---- ----'):
				m.d.comb += self.opcode.eq(Opcodes.ADDLW)

		return m
