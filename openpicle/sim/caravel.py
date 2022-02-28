# SPDX-License-Identifier: BSD-3-Clause
from arachne.core.sim import sim_case
from amaranth import Record
from amaranth.hdl.rec import DIR_FANIN, DIR_FANOUT
from amaranth.sim import Simulator, Settle

from ..caravel import PIC16Caravel

__all__ = (
	'execute1Cycle',
)

flashBus = Record(
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
		assert name == 'spi_flash_4x'
		assert number == 0
		return flashBus

@sim_case(
	domains = (('sync', 25e6),),
	dut = PIC16Caravel(),
	platform = Platform()
)
def sanityCheck(sim : Simulator, dut : PIC16Caravel):
	def writeInstruction(value):
		# Wait for the beginning of the iRead cycle
		while (yield dut.run) == 1:
			yield
		# 4 + ((24 / 4) * 2) + 8 cycles to waste
		for _ in range(24):
			yield
		# Write out the instruction
		for i in range(2):
			shift = i * 8
			yield flashBus.dq.i.eq((value >> (shift + 4)) & 0xF)
			yield
			yield
			yield flashBus.dq.i.eq((value >> shift) & 0xF)
			yield
			yield
		while (yield dut.run) != 1:
			yield

	def domainSync():
		while (yield dut.run) != 1:
			yield
		# Execute MOVLW 0x1F
		yield from writeInstruction(0b11_0000_0001_1111)
		# Execute MOVWF 0x01
		yield from writeInstruction(0b00_0000_1000_0001)
		# Wait for the beginning of the iRead cycle
		while (yield dut.run) == 1:
			yield
		# Check pBus.writeData is the expected value
		yield (dut.peripheral_write_data) == 0x1F
		yield
		yield
		yield
		yield
	yield domainSync, 'sync'
