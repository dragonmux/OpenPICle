# SPDX-License-Identifier: BSD-3-Clause
from torii import Elaboratable, Module, Signal, Memory

class CallStack(Elaboratable):
	def __init__(self):
		self.valueIn = Signal(12)
		self.valueOut = Signal(12)
		self.push = Signal()
		self.pop = Signal()
		self.count = Signal(range(8))

	def elaborate(self, platform):
		m = Module()
		# The PIC16 calls for an 8-entry call stack.
		m.submodules.stack = stack = Memory(width = 12, depth = 8)
		readPort = stack.read_port(domain = "comb")
		writePort = stack.write_port()

		with m.If(self.push):
			m.d.sync += self.count.eq(self.count + 1)
		with m.Elif(self.pop):
			m.d.sync += self.count.eq(self.count - 1)

		m.d.comb += [
			writePort.addr.eq(self.count),
			writePort.data.eq(self.valueIn),
			writePort.en.eq(self.push),
			readPort.addr.eq(self.count - 1),
			self.valueOut.eq(readPort.data),
		]
		return m
