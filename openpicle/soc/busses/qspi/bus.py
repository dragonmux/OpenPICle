# SPDX-License-Identifier: BSD-3-Clause
from amaranth import Elaboratable, Module, Signal, Repl
from .type import *

__all__ = (
	'Bus',
)

class Bus(Elaboratable):
	def __init__(self, *, resource):
		self._bus = resource
		self.cs = Signal()
		self.copi = Signal(8)
		self.cipo = Signal(8)
		self.ready = Signal()
		self.begin = Signal()
		self.rnw = Signal()
		self.complete = Signal()

	def elaborate(self, platform) -> Module:
		m = Module()
		bus = self._bus
		data = Signal.like(self.copi)
		bitCounter = Signal(range(8))
		nibbleCounter = Signal(range(2))
		write = Signal()
		io_i = bus.dq.i
		io_o = bus.dq.o
		io_oe = bus.dq.oe
		cs = Signal()
		copi = bus.dq.o[0]

		m.d.comb += [
			self.complete.eq(0),
			bus.cs.o.eq(self.cs | cs),
			self.cipo.eq(data)
		]

		with m.FSM(name = 'qspi-fsm'):
			# Begin bringup by putting the Flash into QSPI mode
			with m.State('STARTUP'):
				m.d.sync += [
					cs.eq(1),
					io_oe.eq(0b0001),
					data.eq(SPIOpcodes.enableQSPI),
				]
				m.next = 'SPI-SHIFT-L'
			with m.State('SPI-SHIFT-L'):
				m.d.sync += [
					bus.clk.o.eq(0),
					copi.eq(data[7]),
					data.eq(data.shift_left(1)),
					bitCounter.eq(bitCounter - 1),
				]
				m.next = 'SPI-SHIFT-H'
			with m.State('SPI-SHIFT-H'):
				m.d.sync += bus.clk.o.eq(1)
				with m.If(bitCounter == 0):
					m.next = 'SPI-FINISH'
				with m.Else():
					m.next = 'SPI-SHIFT-L'
			with m.State('SPI-FINISH'):
				m.d.sync += [
					cs.eq(0),
					io_oe.eq(0b0000),
					self.ready.eq(1),
				]
				m.next = 'IDLE'

			with m.State('IDLE'):
				with m.If(self.begin):
					m.d.sync += write.eq(~self.rnw)
					with m.If(self.rnw):
						m.d.sync += data.eq(0)
					with m.Else():
						m.d.sync += data.eq(self.copi)
					m.next = 'QSPI-SHIFT-L'
			with m.State('QSPI-SHIFT-L'):
				m.d.sync += [
					bus.clk.o.eq(0),
					io_oe.eq(Repl(write, 4)),
					data.eq(data.shift_left(4)),
					nibbleCounter.eq(nibbleCounter - 1),
				]
				with m.If(write):
					m.d.sync += io_o.eq(data[4:8])
				m.next = 'QSPI-SHIFT-H'
			with m.State('QSPI-SHIFT-H'):
				m.d.sync += bus.clk.o.eq(1)
				with m.If(~write):
					m.d.sync += data[0:4].eq(io_i)
				with m.If(nibbleCounter == 0):
					m.d.comb += self.complete.eq(1)
					with m.If(self.begin):
						m.d.sync += write.eq(~self.rnw)
						with m.If(~self.rnw):
							m.d.sync += data.eq(self.copi)
						m.next = 'QSPI-SHIFT-L'
					with m.Else():
						m.next = 'IDLE'
				with m.Else():
					m.next = 'QSPI-SHIFT-L'
		return m
