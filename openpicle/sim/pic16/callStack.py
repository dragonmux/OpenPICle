# SPDX-License-Identifier: BSD-3-Clause
from arachne.core.sim import sim_case
from nmigen.sim import Simulator
from ...pic16.callStack import CallStack

@sim_case(
	domains = (('sync', 25e6),),
	dut = CallStack()
)
def callStack(sim : Simulator, dut : CallStack):
	def domainSync():
		yield
		yield
		yield dut.valueIn.eq(0x713)
		yield dut.push.eq(1)
		assert (yield dut.count) == 0
		yield
		yield dut.push.eq(0)
		assert (yield dut.count) == 0
		yield
		yield dut.valueIn.eq(0xA5F)
		yield dut.push.eq(1)
		assert (yield dut.count) == 1
		yield
		yield dut.push.eq(0)
		assert (yield dut.count) == 1
		yield
		yield dut.pop.eq(1)
		assert (yield dut.count) == 2
		yield
		yield dut.pop.eq(0)
		assert (yield dut.count) == 2
		assert (yield dut.valueOut) == 0xA5F
		yield
		assert (yield dut.count) == 1
		yield
		yield dut.valueIn.eq(0x975)
		yield dut.push.eq(1)
		assert (yield dut.count) == 1
		yield
		yield dut.push.eq(0)
		assert (yield dut.count) == 1
		yield
		yield dut.pop.eq(1)
		assert (yield dut.count) == 2
		yield
		yield dut.pop.eq(0)
		assert (yield dut.count) == 2
		assert (yield dut.valueOut) == 0x975
		yield
		yield dut.pop.eq(1)
		assert (yield dut.count) == 1
		yield
		yield dut.pop.eq(0)
		assert (yield dut.count) == 1
		assert (yield dut.valueOut) == 0x713
		yield
		assert (yield dut.count) == 0
		yield
	yield domainSync, 'sync'
