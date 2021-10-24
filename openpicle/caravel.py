# SPDX-License-Identifier: BSD-3-Clause
from nmigen import Elaboratable, Module, Signal
# from .pic16 import PIC16

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
		from .pic16.alu import LogicOpcode
		from .pic16.bitmanip import BitOpcode
		self.lhs = Signal(8)
		self.rhs = Signal(8)
		self.carryIn = Signal()
		self.targetBit = Signal(3)

		self.logicResult = Signal(8)
		self.bitResult = Signal(8)
		self.carryOut = Signal()

		self.enable = Signal()
		self.logicOpcode = Signal(LogicOpcode)
		self.bitOpcode = Signal(BitOpcode)

	def elaborate(self, platform):
		from .pic16.alu import LogicUnit
		from .pic16.bitmanip import Bitmanip
		m = Module()
		logicUnit = LogicUnit()
		m.submodules += logicUnit
		bitmanip = Bitmanip()
		m.submodules += bitmanip
		m.d.comb += [
			logicUnit.lhs.eq(self.lhs),
			logicUnit.rhs.eq(self.rhs),
			self.logicResult.eq(logicUnit.result),

			logicUnit.enable.eq(self.enable),
			logicUnit.operation.eq(self.logicOpcode),

			bitmanip.value.eq(self.rhs),
			bitmanip.carryIn.eq(self.carryIn),
			bitmanip.targetBit.eq(self.targetBit),
			self.bitResult.eq(bitmanip.result),
			self.carryOut.eq(bitmanip.carryOut),

			bitmanip.enable.eq(self.enable),
			bitmanip.operation.eq(self.bitOpcode),
		]
		return m

	def get_ports(self):
		return [
			self.lhs,
			self.rhs,
			self.carryIn,
			self.targetBit,

			self.logicResult,
			self.bitResult,
			self.carryOut,

			self.enable,
			self.logicOpcode,
			self.bitOpcode,
		]
