# SPDX-License-Identifier: BSD-3-Clause
from amaranth import Elaboratable, Module, Signal, Cat
from .types import BitOpcode

__all__ = ["Bitmanip"]

class Bitmanip(Elaboratable):
	def __init__(self):
		self.value = Signal(8)
		self.carryIn = Signal()
		self.targetBit = Signal(3)
		self.result = Signal(8)
		self.carryOut = Signal()

		self.enable = Signal()
		self.operation = Signal(BitOpcode)

	def elaborate(self, platform):
		m = Module()
		value = self.value
		result = Signal(9, name = 'answer')

		with m.If(self.enable):
			with m.Switch(self.operation):
				with m.Case(BitOpcode.ROTR):
					m.d.comb += result.eq(Cat(value[1:], self.carryIn, value[0]))
				with m.Case(BitOpcode.ROTL):
					m.d.comb += result.eq(Cat(self.carryIn, value))
				with m.Case(BitOpcode.SWAP):
					m.d.comb += result.eq(Cat(value[4:8], value[0:4], 0))
				with m.Case(BitOpcode.BITCLR):
					m.d.comb += [
						result.eq(value),
						result.bit_select(self.targetBit, 1).eq(0)
					]
				with m.Case(BitOpcode.BITSET):
					m.d.comb += [
						result.eq(value),
						result.bit_select(self.targetBit, 1).eq(1)
					]

		m.d.comb += [
			self.result.eq(result[0:8]),
			self.carryOut.eq(result[8])
		]
		return m
