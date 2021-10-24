# SPDX-License-Identifier: BSD-3-Clause
from nmigen import Elaboratable, Module, Signal

__all__ = (
	'PIC16Caravel',
)

class PIC16Caravel(Elaboratable):
	def __init__(self):
		self.instruction_addr = Signal(12)
		self.instruction_data = Signal(14)
		self.instruction_read = Signal()

	def elaborate(self, platform):
		from .pic16 import PIC16
		m = Module()
		m.submodules.pic = pic = PIC16()
		m.d.comb += [
			self.instruction_addr.eq(pic.iBus.address),
			pic.iBus.data.eq(self.instruction_data),
			self.instruction_read.eq(pic.iBus.read),
		]
		return m

	def get_ports(self):
		return [
			self.instruction_addr,
			self.instruction_data,
			self.instruction_read
		]
