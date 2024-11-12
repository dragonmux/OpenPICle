# SPDX-License-Identifier: BSD-3-Clause
from torii.test import ToriiTestCase
from torii import Record
from torii.hdl.rec import DIR_FANIN, DIR_FANOUT

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

class TestCaravel(ToriiTestCase):
	dut: PIC16Caravel = PIC16Caravel
	domains = (('sync', 25e6),)
	platform = Platform()

	def writeInstruction(self, value):
		# Wait for the beginning of the iRead cycle
		while (yield self.dut.run) == 1:
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
		while (yield self.dut.run) != 1:
			yield

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def testSanityCheck(self):
		while (yield self.dut.run) != 1:
			yield
		# Execute MOVLW 0x1F
		yield from self.writeInstruction(0b11_0000_0001_1111)
		# Execute MOVWF 0x01
		yield from self.writeInstruction(0b00_0000_1000_0001)
		# Wait for the beginning of the iRead cycle
		while (yield self.dut.run) == 1:
			yield
		# Check pBus.writeData is the expected value
		yield (self.dut.peripheral_write_data) == 0x1F
		yield
		yield
		yield
		yield
