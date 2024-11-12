# SPDX-License-Identifier: BSD-3-Clause
from torii.test import ToriiTestCase
from ...pic16.callStack import CallStack

class TestCallStack(ToriiTestCase):
	dut: CallStack = CallStack
	domains = (('sync', 25e6),)

	@ToriiTestCase.simulation
	@ToriiTestCase.sync_domain(domain = 'sync')
	def testCallStack(self):
		yield
		yield
		yield self.dut.valueIn.eq(0x713)
		yield self.dut.push.eq(1)
		assert (yield self.dut.count) == 0
		yield
		yield self.dut.push.eq(0)
		assert (yield self.dut.count) == 0
		yield
		yield self.dut.valueIn.eq(0xA5F)
		yield self.dut.push.eq(1)
		assert (yield self.dut.count) == 1
		yield
		yield self.dut.push.eq(0)
		assert (yield self.dut.count) == 1
		yield
		yield self.dut.pop.eq(1)
		assert (yield self.dut.count) == 2
		yield
		yield self.dut.pop.eq(0)
		assert (yield self.dut.count) == 2
		assert (yield self.dut.valueOut) == 0xA5F
		yield
		assert (yield self.dut.count) == 1
		yield
		yield self.dut.valueIn.eq(0x975)
		yield self.dut.push.eq(1)
		assert (yield self.dut.count) == 1
		yield
		yield self.dut.push.eq(0)
		assert (yield self.dut.count) == 1
		yield
		yield self.dut.pop.eq(1)
		assert (yield self.dut.count) == 2
		yield
		yield self.dut.pop.eq(0)
		assert (yield self.dut.count) == 2
		assert (yield self.dut.valueOut) == 0x975
		yield
		yield self.dut.pop.eq(1)
		assert (yield self.dut.count) == 1
		yield
		yield self.dut.pop.eq(0)
		assert (yield self.dut.count) == 1
		assert (yield self.dut.valueOut) == 0x713
		yield
		assert (yield self.dut.count) == 0
		yield
