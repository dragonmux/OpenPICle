# SPDX-License-Identifier: BSD-3-Clause
from nmigen import Elaboratable, Module, Signal
# from .pic16 import PIC16
from .pic16.bitmanip import Bitmanip, BitOpcode

__all__ = (
	'PIC16Caravel',
)

# class PIC16Caravel(Elaboratable):
# 	def __init__(self):
# 		self.instruction_addr = Signal(12)
# 		self.instruction_data = Signal(14)
# 		self.instruction_read = Signal()

# 	def elaborate(self, platform):
# 		m = Module()
# 		m.submodules.pic = pic = PIC16()
# 		m.d.comb += [
# 			self.instruction_addr.eq(pic.iBus.address),
# 			pic.iBus.data.eq(self.instruction_data),
# 			self.instruction_read.eq(pic.iBus.read),
# 		]
# 		return m

# 	def get_ports(self):
# 		return [
# 			self.instruction_addr,
# 			self.instruction_data,
# 			self.instruction_read
# 		]

class PIC16Caravel(Elaboratable):
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
		bitmanip = Bitmanip()
		m.submodules += bitmanip
		m.d.comb += [
			bitmanip.value.eq(self.value),
			bitmanip.carryIn.eq(self.carryIn),
			bitmanip.targetBit.eq(self.targetBit),
			self.result.eq(bitmanip.result),
			self.carryOut.eq(bitmanip.carryOut),
			bitmanip.enable.eq(self.enable),
			bitmanip.operation.eq(self.operation),
		]
		return m

	def get_ports(self):
		return [
			self.value,
			self.carryIn,
			self.targetBit,
			self.result,
			self.carryOut,

			self.enable,
			self.operation,
		]
