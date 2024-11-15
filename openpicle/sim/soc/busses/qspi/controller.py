# SPDX-License-Identifier: BSD-3-Clause
from torii.test import ToriiTestCase
from torii import Record
from torii.hdl.rec import DIR_FANIN, DIR_FANOUT
from torii.sim import Settle

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
		('dq', [
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
	assert (yield bus.dq.oe) == 0b1111
	yield
	yield Settle()
	assert (yield bus.dq.o) == (data >> 4) & 0xF
	assert (yield bus.clk.o) == 1
	yield
	yield Settle()
	assert (yield bus.clk.o) == 0
	assert (yield bus.dq.oe) == 0b1111
	yield
	yield Settle()
	assert (yield bus.dq.o) == data & 0xF
	assert (yield bus.clk.o) == 1

def qspiWrite(data):
	yield
	yield Settle()
	assert (yield bus.clk.o) == 0
	assert (yield bus.dq.oe) == 0b0000
	yield bus.dq.i.eq((data >> 4) & 0xF)
	yield
	yield Settle()
	assert (yield bus.clk.o) == 1
	yield
	yield Settle()
	assert (yield bus.clk.o) == 0
	assert (yield bus.dq.oe) == 0b0000
	yield bus.dq.i.eq(data & 0xF)
	yield
	yield Settle()
	assert (yield bus.clk.o) == 1

class TestQSPIController(ToriiTestCase):
	dut: Controller = Controller
	dut_args = {
		'resourceName': ('qspi-flash', 0)
	}
	domains = (('sync', 25e6),)
	platform = Platform()

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def testReadByte(self):
		while (yield self.dut.ready) == 0:
			yield
		yield self.dut.address.eq(0x012345)
		yield self.dut.read.eq(1)
		yield
		yield Settle()
		assert (yield bus.cs.o) == 1
		yield self.dut.read.eq(0)
		yield from qspiRead(QSPIOpcodes.fastRead)
		yield from qspiRead(0x01)
		yield from qspiRead(0x23)
		yield from qspiRead(0x45)
		yield from qspiRead(0x00)
		yield from qspiRead(0x00)
		yield from qspiWrite(0xE9)
		yield from qspiWrite(0x5A)
		assert (yield self.dut.complete) == 1
		yield
		yield Settle()
		assert (yield bus.cs.o) == 0
		yield
		assert (yield self.dut.data) == 0x5AE9
		yield
		yield Settle()
		yield
