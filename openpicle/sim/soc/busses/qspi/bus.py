# SPDX-License-Identifier: BSD-3-Clause
from torii.test import ToriiTestCase
from torii import Elaboratable, Module, Signal, ResetSignal, Record
from torii.hdl.rec import DIR_FANIN, DIR_FANOUT
from torii.sim import Settle

from .....soc.busses.qspi.bus import Bus
from .....soc.busses.qspi.type import SPIOpcodes

__all__ = (
	'startup',
)

bus = Record(
	layout = (
		('cs', [
			('o', 1, DIR_FANOUT),
		]),
		('clk', [
			('o', 1, DIR_FANOUT),
		]),
		('dq', [
			('i', 4, DIR_FANIN),
			('o', 4, DIR_FANOUT),
			('oe', 4, DIR_FANOUT),
		]),
	)
)

class DUT(Elaboratable):
	def __init__(self, *, resource):
		self._dut = Bus(resource = resource)
		self._bus = self._dut._bus
		self.cs = self._dut.cs
		self.copi = self._dut.copi
		self.cipo = self._dut.cipo
		self.ready = self._dut.ready
		self.begin = self._dut.begin
		self.rnw = self._dut.rnw
		self.complete = self._dut.complete
		self.reset = Signal()

	def elaborate(self, platform) -> Module:
		m = Module()
		m.submodules.bus = self._dut
		m.d.comb += ResetSignal().eq(self.reset)
		return m

class TestQSPIBus(ToriiTestCase):
	dut: DUT = DUT
	dut_args = {
		'resource': bus
	}
	domains = (('sync', 25e6),)

	def performIO(self, *, dataOut):
		bus = self.dut._bus
		copi = bus.dq.o[0]
		yield
		yield Settle()
		assert (yield bus.cs.o) == 1
		assert (yield bus.dq.oe) == 0b0001
		for i in range(8):
			yield
			yield Settle()
			assert (yield bus.clk.o) == 0
			assert (yield copi) == (dataOut >> (7 - i)) & 1
			yield
			yield Settle()
			assert (yield bus.clk.o) == 1
		assert (yield bus.cs.o) == 1
		assert (yield bus.dq.oe) == 0b0001
		yield
		yield Settle()
		assert (yield self.dut.ready) == 1
		assert (yield bus.cs.o) == 0
		assert (yield bus.dq.oe) == 0b0000
		yield
		yield Settle()

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def testStartup(self):
		bus = self.dut._bus
		reset = self.dut.reset

		yield reset.eq(1)
		yield Settle()
		yield
		yield self.dut.cs.eq(0)
		yield
		yield Settle()
		assert (yield self.dut.ready) == 0
		assert (yield bus.cs.o) == 0
		assert (yield bus.dq.oe) == 0b0000
		yield reset.eq(0)
		yield from self.performIO(dataOut = SPIOpcodes.enableQSPI)
		assert (yield self.dut.ready) == 1
		assert (yield bus.cs.o) == 0
		assert (yield bus.dq.oe) == 0b0000
		yield
		yield Settle()
		assert (yield bus.cs.o) == 0
		assert (yield bus.dq.oe) == 0b0000
