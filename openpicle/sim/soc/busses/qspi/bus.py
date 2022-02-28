# SPDX-License-Identifier: BSD-3-Clause
from arachne.core.sim import sim_case
from amaranth import Elaboratable, Module, Signal, ResetSignal, Record
from amaranth.hdl.rec import DIR_FANIN, DIR_FANOUT
from amaranth.sim import Simulator, Settle

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

@sim_case(
	domains = (('sync', 25e6),),
	dut = DUT(resource = bus)
)
def startup(sim : Simulator, dut : DUT):
	bus = dut._bus
	reset = dut.reset
	copi = bus.dq.o[0]

	def performIO(*, dataOut):
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
		assert (yield dut.ready) == 1
		assert (yield bus.cs.o) == 0
		assert (yield bus.dq.oe) == 0b0000
		yield
		yield Settle()

	def domainSync():
		yield reset.eq(1)
		yield Settle()
		yield
		yield dut.cs.eq(0)
		yield
		yield Settle()
		assert (yield dut.ready) == 0
		assert (yield bus.cs.o) == 0
		assert (yield bus.dq.oe) == 0b0000
		yield reset.eq(0)
		yield from performIO(dataOut = SPIOpcodes.enableQSPI)
		assert (yield dut.ready) == 1
		assert (yield bus.cs.o) == 0
		assert (yield bus.dq.oe) == 0b0000
		yield
		yield Settle()
		assert (yield bus.cs.o) == 0
		assert (yield bus.dq.oe) == 0b0000
	yield domainSync, 'sync'
