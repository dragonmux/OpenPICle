# SPDX-License-Identifier: BSD-3-Clause
from torii import Elaboratable, Module, Signal, ResetInserter, EnableInserter

__all__ = (
	'PIC16Caravel',
)

class PIC16Caravel(Elaboratable):
	def elaborate(self, platform):
		from .pic16 import PIC16
		from .soc.busses.qspi import QSPIBus
		m = Module()
		reset = Signal()
		busy_n = Signal(reset = 1)

		m.submodules.qspiFlash = qspiFlash = QSPIBus(resourceName = ('spi_flash_4x', 0))
		m.submodules.pic = pic = ResetInserter(reset)(EnableInserter(busy_n)(PIC16()))

		run = platform.request('run', 0)
		pBus = platform.request('p_bus', 0)
		addr = pBus.addr.o
		dataIn = pBus.data.i
		dataOut = pBus.data.o
		dataDir = pBus.data.oe
		read = pBus.read
		write = pBus.write

		with m.If(qspiFlash.complete | reset):
			m.d.sync += busy_n.eq(1)
		with m.Elif(pic.iBus.read):
			m.d.sync += busy_n.eq(0)

		m.d.comb += [
			reset.eq(~qspiFlash.ready),
			run.o.eq(qspiFlash.ready & busy_n),

			qspiFlash.address[0].eq(0),
			qspiFlash.address[1:].eq(pic.iBus.address),
			pic.iBus.data.eq(qspiFlash.data),
			qspiFlash.read.eq(pic.iBus.read),

			addr.eq(pic.pBus.address),
			read.eq(pic.pBus.read),
			pic.pBus.readData.eq(dataIn),
			write.eq(pic.pBus.write),
			dataOut.eq(pic.pBus.writeData),
			dataDir.eq(pic.pBus.write),
		]
		return m

	def get_ports(self):
		return []
