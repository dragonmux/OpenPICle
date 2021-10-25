# SPDX-License-Identifier: BSD-3-Clause
from arachne.core.sim import sim_case
from nmigen import Record
from nmigen.hdl.rec import DIR_FANIN, DIR_FANOUT
from nmigen.sim import Simulator, Settle

from .....soc.busses.qspi.type import QSPIOpcodes
from .....soc.busses.qspi.controller import Controller

__all__ = (
	'readByte',
)

bus = Record(
	layout = (
		('cs', [
			('o', 1, DIR_FANOUT),
		]),
		('clk', [
			('o', 1, DIR_FANOUT),
		]),
		('io', [
			('i', 4, DIR_FANIN),
			('o', 4, DIR_FANOUT),
			('oe', 4, DIR_FANOUT),
		]),
	)
)

class Platform:
	@property
	def default_clk_frequency(self):
		return float(25e6)

	def request(self, name, number):
		assert name == 'qspi-flash'
		assert number == 0
		return bus

def qspiRead(data):
	yield
	yield Settle()
	assert (yield bus.clk.o) == 0
	assert (yield bus.io.oe) == 0b1111
	yield
	yield Settle()
	assert (yield bus.io.o) == (data >> 4) & 0xF
	assert (yield bus.clk.o) == 1
	yield
	yield Settle()
	assert (yield bus.clk.o) == 0
	assert (yield bus.io.oe) == 0b1111
	yield
	yield Settle()
	assert (yield bus.io.o) == data & 0xF
	assert (yield bus.clk.o) == 1

def qspiWrite(data):
	yield
	yield Settle()
	assert (yield bus.clk.o) == 0
	assert (yield bus.io.oe) == 0b0000
	yield bus.io.i.eq((data >> 4) & 0xF)
	yield
	yield Settle()
	assert (yield bus.clk.o) == 1
	yield
	yield Settle()
	assert (yield bus.clk.o) == 0
	assert (yield bus.io.oe) == 0b0000
	yield bus.io.i.eq(data & 0xF)
	yield
	yield Settle()
	assert (yield bus.clk.o) == 1

@sim_case(
	domains = (('sync', 25e6),),
	dut = Controller(resourceName = ('qspi-flash', 0)),
	platform = Platform()
)
def readByte(sim : Simulator, dut : Controller):
	def domainSync():
		while (yield dut.ready) == 0:
			yield
		yield dut.address.eq(0x012345)
		yield dut.read.eq(1)
		yield
		yield Settle()
		assert (yield bus.cs.o) == 1
		yield dut.read.eq(0)
		yield from qspiRead(QSPIOpcodes.fastRead)
		yield from qspiRead(0x01)
		yield from qspiRead(0x23)
		yield from qspiRead(0x45)
		yield from qspiRead(0x00)
		yield from qspiRead(0x00)
		yield from qspiWrite(0xE9)
		yield
		yield Settle()
		assert (yield bus.cs.o) == 0
		assert (yield dut.complete) == 1
		assert (yield dut.data) == 0xE9
		yield
		yield Settle()
		yield
	yield domainSync, 'sync'
