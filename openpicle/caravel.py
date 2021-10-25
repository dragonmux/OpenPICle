# SPDX-License-Identifier: BSD-3-Clause
from nmigen import Elaboratable, Module, Signal, ResetInserter, EnableInserter

__all__ = (
	'PIC16Caravel',
)

class PIC16Caravel(Elaboratable):
	def __init__(self):
		self.run = Signal()

		self.peripheral_addr = Signal(7)
		self.peripheral_read_data = Signal(8)
		self.peripheral_read = Signal()
		self.peripheral_write_data = Signal(8)
		self.peripheral_write = Signal()

	def elaborate(self, platform):
		from .pic16 import PIC16
		from .soc.busses.qspi import QSPIBus
		m = Module()
		reset = Signal()
		busy_n = Signal(reset = 1)

		m.submodules.qspiFlash = qspiFlash = QSPIBus(resourceName = ('spi_flash_4x', 0))
		m.submodules.pic = pic = ResetInserter(reset)(EnableInserter(busy_n)(PIC16()))

		with m.If(qspiFlash.complete | reset):
			m.d.sync += busy_n.eq(1)
		with m.Elif(pic.iBus.read):
			m.d.sync += busy_n.eq(0)

		m.d.comb += [
			reset.eq(~qspiFlash.ready),
			self.run.eq(qspiFlash.ready & busy_n),

			qspiFlash.address[0].eq(0),
			qspiFlash.address[1:].eq(pic.iBus.address),
			pic.iBus.data.eq(qspiFlash.data),
			qspiFlash.read.eq(pic.iBus.read),

			self.peripheral_addr.eq(pic.pBus.address),
			self.peripheral_read.eq(pic.pBus.read),
			pic.pBus.readData.eq(self.peripheral_read_data),
			self.peripheral_write.eq(pic.pBus.write),
			self.peripheral_write_data.eq(pic.pBus.writeData),
		]
		return m

	def get_ports(self):
		return [
			self.run,

			self.peripheral_addr,
			self.peripheral_read_data,
			self.peripheral_read,
			self.peripheral_write_data,
			self.peripheral_write,
		]
