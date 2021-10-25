# SPDX-License-Identifier: BSD-3-Clause
from typing import Tuple, Union
from nmigen import Elaboratable, Module, Signal

from .bus import Bus
from .type import QSPIOpcodes

__all__ = (
	'Controller',
)

class Controller(Elaboratable):
	def __init__(self, resourceName : Union[Tuple[str], Tuple[str, int]]):
		self.address = Signal(24)
		self.data = Signal(8)
		self.ready = Signal()
		self.read = Signal()
		self.complete = Signal()

		self._resourceName = resourceName

	def elaborate(self, platform) -> Module:
		m = Module()
		m.submodules.bus = bus = Bus(resource = platform.request(*self._resourceName))
		dummyCounter = Signal(range(2))

		m.d.comb += [
			self.complete.eq(0),
			self.ready.eq(bus.ready),
		]

		with m.FSM(name = 'flash-fsm'):
			with m.State('IDLE'):
				with m.If(self.read):
					# As soon as we get asked to read something, issue the command to the Flash
					m.d.sync += bus.cs.eq(1)
					m.d.comb += [
						bus.begin.eq(1),
						bus.rnw.eq(0),
						bus.copi.eq(QSPIOpcodes.fastRead),
					]
					m.next = 'ISSUE-ADDR-H'
			with m.State('ISSUE-ADDR-H'):
				with m.If(bus.complete):
					m.d.comb += [
						bus.begin.eq(1),
						bus.rnw.eq(0),
						bus.copi.eq(self.address[16:24]),
					]
					m.next = 'ISSUE-ADDR-M'
			with m.State('ISSUE-ADDR-M'):
				with m.If(bus.complete):
					m.d.comb += [
						bus.begin.eq(1),
						bus.rnw.eq(0),
						bus.copi.eq(self.address[8:16]),
					]
					m.next = 'ISSUE-ADDR-L'
			with m.State('ISSUE-ADDR-L'):
				with m.If(bus.complete):
					m.d.comb += [
						bus.begin.eq(1),
						bus.rnw.eq(0),
						bus.copi.eq(self.address[0:8]),
					]
					m.next = 'ISSUE-DUMMY'
			with m.State('ISSUE-DUMMY'):
				with m.If(bus.complete):
					m.d.sync += dummyCounter.eq(dummyCounter - 1)
					m.d.comb += [
						bus.begin.eq(1),
						bus.rnw.eq(0),
						bus.copi.eq(0),
					]
					with m.If(dummyCounter == 1):
						m.next = 'ISSUE-DATA'
			with m.State('ISSUE-DATA'):
				with m.If(bus.complete):
					m.d.comb += [
						bus.begin.eq(1),
						bus.rnw.eq(1),
					]
					m.next = 'ISSUE-DATA-WAIT'
			with m.State('ISSUE-DATA-WAIT'):
				with m.If(bus.complete):
					m.next = 'ISSUE-DELAY'
			with m.State('ISSUE-DELAY'):
				m.d.sync += [
					bus.cs.eq(0),
					self.data.eq(bus.cipo),
				]
				m.next = 'COMPLETE'
			with m.State('COMPLETE'):
				m.d.comb += self.complete.eq(1)
				m.next = 'IDLE'
		return m
