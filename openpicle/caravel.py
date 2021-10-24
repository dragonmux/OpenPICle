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

		self.peripheral_addr = Signal(7)
		self.peripheral_read_data = Signal(8)
		self.peripheral_read = Signal()
		self.peripheral_write_data = Signal(8)
		self.peripheral_write = Signal()

	def elaborate(self, platform):
		from .pic16 import PIC16
		m = Module()
		m.submodules.pic = pic = PIC16()
		m.d.comb += [
			self.instruction_addr.eq(pic.iBus.address),
			pic.iBus.data.eq(self.instruction_data),
			self.instruction_read.eq(pic.iBus.read),

			self.peripheral_addr.eq(pic.pBus.address),
			self.peripheral_read.eq(pic.pBus.read),
			pic.pBus.readData.eq(self.peripheral_read_data),
			self.peripheral_write.eq(pic.pBus.write),
			self.peripheral_write_data.eq(pic.pBus.writeData),
		]
		return m

	def get_ports(self):
		return [
			self.instruction_addr,
			self.instruction_data,
			self.instruction_read,

			self.peripheral_addr,
			self.peripheral_read_data,
			self.peripheral_read,
			self.peripheral_write_data,
			self.peripheral_write,
		]
