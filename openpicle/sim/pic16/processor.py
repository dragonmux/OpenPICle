# SPDX-License-Identifier: BSD-3-Clause
from arachne.core.sim import sim_case
from amaranth.sim import Simulator, Settle
from ...pic16 import PIC16

@sim_case(
	domains = (('sync', 25e6),),
	dut = PIC16()
)
def processor(sim : Simulator, dut : PIC16):
	iBus = dut.iBus
	pBus = dut.pBus

	def domainSync():
		assert (yield iBus.read) == 1
		assert (yield iBus.address) == 0
		assert (yield dut.pc) == 0
		# Perform NOP
		yield iBus.data.eq(0b00_0000_0000_0000)
		yield Settle()
		yield
		yield Settle()
		assert (yield iBus.read) == 0
		yield
		yield Settle()
		assert (yield iBus.read) == 0
		yield
		yield Settle()
		assert (yield iBus.read) == 1
		# Perform MOVLW 0x1F
		yield iBus.data.eq(0b11_0000_0001_1111)
		yield Settle()
		yield
		yield Settle()
		assert (yield iBus.read) == 0
		yield
		yield Settle()
		assert (yield iBus.read) == 0
		yield
		yield
		yield Settle()
		assert (yield iBus.read) == 1
		# Perform ADDLW 5
		yield iBus.data.eq(0b11_1110_0000_0101)
		yield Settle()
		yield
		yield Settle()
		assert (yield dut.wreg) == 0x1F
		assert (yield iBus.read) == 0
		yield
		yield Settle()
		assert (yield iBus.read) == 0
		yield
		yield
		yield Settle()
		assert (yield iBus.read) == 1
		# Perform ADDWF 5,f
		yield iBus.data.eq(0b00_0111_1000_0101)
		yield Settle()
		yield
		yield Settle()
		assert (yield dut.wreg) == 0x24
		assert (yield iBus.read) == 0
		yield
		yield Settle()
		assert (yield pBus.read) == 1
		assert (yield iBus.read) == 0
		yield pBus.readData.eq(0x20)
		yield Settle()
		yield
		yield Settle()
		assert (yield pBus.read) == 0
		yield
		yield Settle()
		assert (yield iBus.read) == 1
		assert (yield pBus.read) == 0
		assert (yield pBus.write) == 0
		# Perform SWAPF 8,f
		yield iBus.data.eq(0b00_1110_1000_1000)
		yield Settle()
		yield
		yield Settle()
		assert (yield dut.wreg) == 0x24
		assert (yield iBus.read) == 0
		assert (yield pBus.write) == 1
		assert (yield pBus.writeData) == 0x44
		yield
		yield Settle()
		assert (yield pBus.write) == 0
		assert (yield pBus.read) == 1
		yield pBus.readData.eq(0x0F)
		yield Settle()
		yield
		yield Settle()
		assert (yield pBus.read) == 0
		yield
		yield Settle()
		assert (yield iBus.read) == 1
		assert (yield pBus.write) == 0
		# Perform RLF 8,w
		yield iBus.data.eq(0b00_1101_0000_1000)
		yield Settle()
		yield
		yield Settle()
		assert (yield iBus.read) == 0
		assert (yield pBus.write) == 1
		assert (yield pBus.writeData) == 0xF0
		yield
		yield Settle()
		assert (yield pBus.write) == 0
		yield pBus.readData.eq(0x80)
		yield Settle()
		assert (yield pBus.read) == 1
		yield
		yield Settle()
		assert (yield pBus.read) == 0
		yield
		yield Settle()
		assert (yield pBus.write) == 0

		# Perform BSF 4, 5
		yield iBus.data.eq(0b01_0110_1000_0100)
		yield Settle()
		yield
		yield Settle()
		assert (yield dut.wreg) == 0
		assert (yield pBus.write) == 0
		yield
		yield Settle()
		assert (yield pBus.write) == 0
		yield
		yield

		# Perform NOP
		yield iBus.data.eq(0b00_0000_0000_0000)
		yield Settle()
		yield
		yield
		yield
		yield

		# Perform NOP
		yield iBus.data.eq(0b00_0000_0000_0000)
		yield
		yield
		yield
		yield

		# Perform CALL 0x015
		yield iBus.data.eq(0b10_0000_0001_0101)
		yield
		assert (yield iBus.address) == 9
		assert (yield dut.pc) == 9
		yield
		yield
		yield

		# Perform RETURN
		yield iBus.data.eq(0b00_0000_0000_1000)
		yield
		assert (yield iBus.address) == 0x015
		assert (yield dut.pc) == 0x015
		yield
		yield
		yield

		# Perform NOP
		yield iBus.data.eq(0b00_0000_0000_0000)
		yield
		assert (yield iBus.address) == 10
		assert (yield dut.pc) == 10
		yield
		yield
		yield
	yield domainSync, 'sync'
