from arachne.core.sim import sim_case
from nmigen import Elaboratable, Signal, Module
from nmigen.sim import Simulator, Settle
from ...pic16.types import ArithOpcode, LogicOpcode
from ...pic16.alu import ArithUnit, LogicUnit

class DUT(Elaboratable):
	def __init__(self):
		self.arithOpcode = Signal(ArithOpcode)
		self.arithLHS = Signal(8)
		self.arithRHS = Signal(8)
		self.arithResult = Signal(8)
		self.logicOpcode = Signal(LogicOpcode)
		self.logicLHS = Signal(8)
		self.logicRHS = Signal(8)
		self.logicResult = Signal(8)
		self.carry = Signal()

	def elaborate(self, platform):
		m = Module()
		m.submodules.arithUnit = arithUnit = ArithUnit()
		m.submodules.logicUnit = logicUnit = LogicUnit()
		carryInvert = Signal()

		m.d.comb += [
			carryInvert.eq((self.arithOpcode == ArithOpcode.SUB) | (self.arithOpcode == ArithOpcode.DEC)),
			arithUnit.operation.eq(self.arithOpcode),
			arithUnit.enable.eq(1),
			arithUnit.lhs.eq(self.arithLHS),
			arithUnit.rhs.eq(self.arithRHS),
			self.arithResult.eq(arithUnit.result),
			self.carry.eq(arithUnit.carry ^ carryInvert),
			logicUnit.enable.eq(1),
			logicUnit.operation.eq(self.logicOpcode),
			logicUnit.lhs.eq(self.logicLHS),
			logicUnit.rhs.eq(self.logicRHS),
			self.logicResult.eq(logicUnit.result),
		]
		return m

@sim_case(
	domains = (('sync', 25e6),),
	dut = DUT()
)
def alu(sim : Simulator, dut : DUT):
	def performArith(opcode, lhs, rhs):
		yield dut.arithOpcode.eq(opcode)
		yield dut.arithLHS.eq(lhs)
		yield dut.arithRHS.eq(rhs)

	def performLogic(opcode, lhs, rhs):
		yield dut.logicOpcode.eq(opcode)
		yield dut.logicLHS.eq(lhs)
		yield dut.logicRHS.eq(rhs)

	def checkResult(arithResult, logicResult, carry):
		yield Settle()
		assert (yield dut.arithResult) == arithResult
		assert (yield dut.logicResult) == logicResult
		assert (yield dut.carry) == carry

	def domainSync():
		yield from performArith(ArithOpcode.ADD, 0, 0)
		yield from performLogic(LogicOpcode.NONE, 0, 0)
		yield
		yield from checkResult(0, 0, 0)
		yield from performArith(ArithOpcode.ADD, 5, 10)
		yield
		yield from checkResult(15, 0, 0)
		yield from performArith(ArithOpcode.ADD, 0, 10)
		yield
		yield from checkResult(10, 0, 0)
		yield from performArith(ArithOpcode.SUB, 35, 10)
		yield
		yield from checkResult(25, 0, 0)
		yield from performArith(ArithOpcode.ADD, 255, 112)
		yield
		yield from checkResult(111, 0, 1)
		yield from performArith(ArithOpcode.INC, 35, 0)
		yield
		yield from checkResult(1, 0, 0)
		yield from performArith(ArithOpcode.ADD, 0, 112)
		yield
		yield from checkResult(112, 0, 0)
		yield from performArith(ArithOpcode.DEC, 196, 254)
		yield
		yield from checkResult(253, 0, 0)
		yield from performArith(ArithOpcode.ADD, 0, 0)
		yield
		yield from checkResult(0, 0, 0)
		yield from performLogic(LogicOpcode.AND, 154, 196)
		yield
		yield from checkResult(0, 128, 0)
		yield from performLogic(LogicOpcode.NONE, 100, 5)
		yield
		yield from checkResult(0, 0, 0)
		yield from performLogic(LogicOpcode.OR, 0xF0, 0x0F)
		yield
		yield from checkResult(0, 255, 0)
		yield from performLogic(LogicOpcode.NONE, 100, 5)
		yield
		yield from checkResult(0, 0, 0)
		yield from performLogic(LogicOpcode.XOR, 0xA5, 0x57)
		yield
		yield from checkResult(0, 0xF2, 0)
		yield from performLogic(LogicOpcode.NONE, 0, 5)
		yield
		yield from checkResult(0, 0, 0)
		yield from performArith(ArithOpcode.ADD, 254, 5)
		yield
		yield from checkResult(3, 0, 1)
		yield from performArith(ArithOpcode.SUB, 1, 5)
		yield
		yield from checkResult(252, 0, 1)
		yield from performArith(ArithOpcode.ADD, 0, 0)
		yield from performLogic(LogicOpcode.OR, 0xA0, 0x05)
		yield
		yield from checkResult(0, 0xA5, 0)
		yield from performLogic(LogicOpcode.NONE, 0, 0)
		yield from performArith(ArithOpcode.INC, 66, 255)
		yield
		yield from checkResult(0, 0, 1)
		yield from performArith(ArithOpcode.DEC, 66, 0)
		yield
		yield from checkResult(255, 0, 1)
		yield from performArith(ArithOpcode.ADD, 66, 54)
		yield
		yield from checkResult(120, 0, 0)
		yield
		yield from checkResult(120, 0, 0)
	yield domainSync, 'sync'
