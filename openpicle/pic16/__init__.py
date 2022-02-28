# SPDX-License-Identifier: BSD-3-Clause
from amaranth import Elaboratable, Module, Signal, unsigned
from .types import Opcodes, ArithOpcode, LogicOpcode, BitOpcode
from .busses import *

__all__ = ["PIC16"]

class PIC16(Elaboratable):
	def __init__(self):
		self.iBus = InstructionBus()
		self.pBus = PeripheralBus()

		self.pcLatchHigh = Signal(8)

		self.wreg = Signal(8)
		self.pc = Signal(12)
		self.flags = Signal(8)

	def elaborate(self, platform):
		from .decoder import Decoder
		from .alu import ArithUnit, LogicUnit
		from .bitmanip import Bitmanip
		from .callStack import CallStack
		m = Module()
		decoder = Decoder()
		m.submodules.decoder = decoder
		arithUnit = ArithUnit()
		m.submodules.arith = arithUnit
		logicUnit = LogicUnit()
		m.submodules.logic = logicUnit
		bitmanip = Bitmanip()
		m.submodules.bitmanip = bitmanip
		callStack = CallStack()
		m.submodules.callStack = callStack

		q = Signal(unsigned(2))
		actualQ = Signal(unsigned(2))
		m.d.sync += q.eq(q + 1)
		m.d.sync += actualQ.eq(q)

		instruction = Signal(14)
		lhs = Signal(8)
		rhs = Signal(8)
		result = Signal(8)
		targetBit = Signal(3)
		opEnable = Signal()
		skip = Signal()
		pause = Signal()
		pcNext = Signal.like(self.pc)

		carry = self.flags[0]
		zero = self.flags[1]

		opcode = Signal(Opcodes)
		arithOpcode = self.mapArithOpcode(m, opcode)
		logicOpcode = self.mapLogicOpcode(m, opcode)
		bitOpcode = self.mapBitmanipOpcode(m, opcode)

		loadsWReg = self.loadsWReg(m, opcode)
		loadsFReg = self.loadsFReg(m, opcode)
		loadsLiteral = self.loadsLiteral(m, opcode)
		storesWReg = Signal()
		storesFReg = Signal()
		changesFlow = self.changesFlow(m, opcode)
		loadPCLatchHigh = self.loadPCLatchHigh(m, opcode)
		isReturn = self.isReturn(m, opcode)
		storesZeroFlag = Signal()

		resultFromArith = Signal()
		resultFromLogic = Signal()
		resultFromBit = Signal()
		resultFromLit = Signal()
		resultFromWReg = Signal()
		resultZero = Signal()
		carryInvert = Signal()

		m.d.comb += opEnable.eq(0)

		with m.Switch(q):
			with m.Case(0):
				with m.If(storesWReg):
					m.d.sync += self.wreg.eq(result)
				with m.Elif(storesFReg):
					m.d.sync += [
						self.pBus.address.eq(instruction[0:7]),
						self.pBus.writeData.eq(result),
						self.pBus.write.eq(1)
					]
				with m.If(storesZeroFlag):
					m.d.sync += zero.eq(skip)

				with m.If(resultFromArith):
					m.d.sync += carry.eq(arithUnit.carry)
				with m.Elif(resultFromBit):
					m.d.sync += carry.eq(bitmanip.carryOut)

				with m.If((opcode == Opcodes.INCFSZ) | (opcode == Opcodes.DECFSZ)):
					m.d.sync += pause.eq(skip)

				m.d.comb += [
					self.iBus.read.eq(1),
					opEnable.eq(1)
				]
			with m.Case(1):
				with m.If(pause):
					m.d.sync += instruction.eq(0), # Load a NOP if we're entering a pause cycle.
				with m.Else():
					m.d.sync += [
						instruction.eq(self.iBus.data),
						self.pBus.address.eq(self.iBus.data[0:7])
					]
				m.d.sync += carry.eq(carry ^ (resultFromArith & carryInvert))

				m.d.sync += self.pBus.write.eq(0)
			with m.Case(2):
				with m.If(pause):
					m.d.sync += pause.eq(0)
				with m.If(loadsFReg):
					m.d.comb += self.pBus.read.eq(1)

				with m.If(opcode == Opcodes.CALL):
					m.d.sync += [
						callStack.valueIn.eq(self.pc + 1),
						callStack.push.eq(1)
					]
				with m.Elif(isReturn):
					m.d.sync += [
						self.pc.eq(callStack.valueOut),
						callStack.pop.eq(1)
					]

				with m.If(loadPCLatchHigh):
					m.d.sync += [
						self.pc[0:11].eq(instruction[0:11]),
						self.pc[11:].eq(self.pcLatchHigh[3:5])
					]
				with m.Elif(~changesFlow):
					m.d.sync += self.pc.eq(pcNext)
			with m.Case(3):
				with m.If(opcode == Opcodes.CALL):
					m.d.sync += callStack.push.eq(0)
				with m.Elif(isReturn):
					m.d.sync += callStack.pop.eq(0)

		with m.If(loadsWReg):
			m.d.sync += lhs.eq(self.wreg)
		with m.Else():
			m.d.sync += lhs.eq(0)

		with m.If(loadsFReg):
			m.d.sync += rhs.eq(self.pBus.readData)
		with m.Elif(loadsLiteral):
			m.d.sync += rhs.eq(instruction[0:8])
		with m.Else():
			m.d.sync += rhs.eq(0)

		with m.If((opcode == Opcodes.BCF) | (opcode == Opcodes.BSF)):
			m.d.sync += targetBit.eq(instruction[7:10])

		with m.If(resultFromArith):
			m.d.comb += result.eq(arithUnit.result)
		with m.Elif(resultFromLogic):
			m.d.comb += result.eq(logicUnit.result)
		with m.Elif(resultFromBit):
			m.d.comb += result.eq(bitmanip.result)
		with m.Elif(resultZero):
			m.d.comb += result.eq(0)
		with m.Elif(resultFromLit):
			m.d.comb += result.eq(rhs)
		with m.Elif(resultFromWReg):
			m.d.comb += result.eq(self.wreg)

		with m.If(~changesFlow):
			m.d.comb += pcNext.eq(self.pc + 1)

		m.d.sync += [
			arithUnit.operation.eq(arithOpcode),
			logicUnit.operation.eq(logicOpcode),
			bitmanip.operation.eq(bitOpcode),
			bitmanip.value.eq(rhs),
			bitmanip.carryIn.eq(carry),
			resultFromArith.eq(self.resultFromArith(m, opcode)),
			resultFromLogic.eq(logicOpcode != LogicOpcode.NONE),
			resultFromBit.eq(bitOpcode != BitOpcode.NONE),
			resultFromLit.eq(opcode == Opcodes.MOVLW),
			resultFromWReg.eq(opcode == Opcodes.MOVWF),
			resultZero.eq((opcode == Opcodes.CLRF) | (opcode == Opcodes.CLRW)),
			storesWReg.eq(self.storesWReg(m, opcode, instruction[7])),
			storesFReg.eq(self.storesFReg(m, opcode, instruction[7])),
			storesZeroFlag.eq(self.storesZeroFlag(m, opcode)),
			carryInvert.eq((arithOpcode == ArithOpcode.SUB) | (arithOpcode == ArithOpcode.DEC)),
		]

		m.d.comb += [
			decoder.instruction.eq(instruction),
			opcode.eq(decoder.opcode),
			arithUnit.enable.eq(opEnable),
			arithUnit.lhs.eq(lhs),
			arithUnit.rhs.eq(rhs),
			skip.eq(arithUnit.result == 0),
			logicUnit.enable.eq(opEnable),
			logicUnit.lhs.eq(lhs),
			logicUnit.rhs.eq(rhs),
			bitmanip.targetBit.eq(targetBit),
			bitmanip.enable.eq(opEnable),
			self.iBus.address.eq(self.pc),
		]
		return m

	def mapArithOpcode(self, m, opcode):
		result = Signal(ArithOpcode, name = "aluOpcode")
		with m.Switch(opcode):
			with m.Case(Opcodes.ADDLW, Opcodes.ADDWF):
				m.d.comb += result.eq(ArithOpcode.ADD)
			with m.Case(Opcodes.SUBLW, Opcodes.SUBWF):
				m.d.comb += result.eq(ArithOpcode.SUB)
			with m.Case(Opcodes.INCF, Opcodes.INCFSZ):
				m.d.comb += result.eq(ArithOpcode.INC)
			with m.Case(Opcodes.DECF, Opcodes.DECFSZ):
				m.d.comb += result.eq(ArithOpcode.DEC)
			with m.Default():
				m.d.comb += result.eq(ArithOpcode.ADD)
		return result

	def resultFromArith(self, m, opcode):
		result = Signal(name = "resultFromArith")
		with m.Switch(opcode):
			with m.Case(
				Opcodes.ADDLW,
				Opcodes.SUBLW,
				Opcodes.INCF,
				Opcodes.DECF,
				Opcodes.ADDWF,
				Opcodes.SUBWF,
				Opcodes.INCFSZ,
				Opcodes.DECFSZ
			):
				m.d.comb += result.eq(1)
			with m.Default():
				m.d.comb += result.eq(0)
		return result

	def mapLogicOpcode(self, m, opcode):
		result = Signal(LogicOpcode, name = "logicOpcode")
		with m.Switch(opcode):
			with m.Case(Opcodes.ANDLW, Opcodes.ANDWF):
				m.d.comb += result.eq(LogicOpcode.AND)
			with m.Case(Opcodes.IORLW, Opcodes.IORWF):
				m.d.comb += result.eq(LogicOpcode.OR)
			with m.Case(Opcodes.XORLW, Opcodes.XORWF):
				m.d.comb += result.eq(LogicOpcode.XOR)
			with m.Default():
				m.d.comb += result.eq(LogicOpcode.NONE)
		return result

	def mapBitmanipOpcode(self, m, opcode):
		result = Signal(BitOpcode, name = "bitOpcode")
		with m.Switch(opcode):
			with m.Case(Opcodes.RRF):
				m.d.comb += result.eq(BitOpcode.ROTR)
			with m.Case(Opcodes.RLF):
				m.d.comb += result.eq(BitOpcode.ROTL)
			with m.Case(Opcodes.SWAPF):
				m.d.comb += result.eq(BitOpcode.SWAP)
			with m.Case(Opcodes.BCF):
				m.d.comb += result.eq(BitOpcode.BITCLR)
			with m.Case(Opcodes.BSF):
				m.d.comb += result.eq(BitOpcode.BITSET)
			with m.Default():
				m.d.comb += result.eq(BitOpcode.NONE)
		return result

	def loadsWReg(self, m, opcode):
		result = Signal(name = "loadsWReg")
		with m.Switch(opcode):
			with m.Case(
				Opcodes.MOVWF,
				Opcodes.ADDWF,
				Opcodes.SUBWF,
				Opcodes.ANDWF,
				Opcodes.IORWF,
				Opcodes.XORWF,
				Opcodes.ADDLW,
				Opcodes.SUBLW,
				Opcodes.ANDLW,
				Opcodes.IORLW,
				Opcodes.XORLW
			):
				m.d.comb += result.eq(1)
			with m.Default():
				m.d.comb += result.eq(0)
		return result

	def loadsFReg(self, m, opcode):
		result = Signal(name = "loadsFReg")
		with m.Switch(opcode):
			with m.Case(
				Opcodes.ADDWF,
				Opcodes.SUBWF,
				Opcodes.ANDWF,
				Opcodes.IORWF,
				Opcodes.XORWF,
				Opcodes.INCF,
				Opcodes.INCFSZ,
				Opcodes.DECF,
				Opcodes.DECFSZ,
				Opcodes.COMF,
				Opcodes.MOVF,
				Opcodes.RLF,
				Opcodes.RRF,
				Opcodes.SWAPF,
				Opcodes.BCF,
				Opcodes.BSF,
				Opcodes.BTFSC,
				Opcodes.BTFSS
			):
				m.d.comb += result.eq(1)
			with m.Default():
				m.d.comb += result.eq(0)
		return result

	def loadsLiteral(self, m, opcode):
		result = Signal(name = "loadsLiteral")
		with m.Switch(opcode):
			with m.Case(
				Opcodes.MOVLW,
				Opcodes.RETLW,
				Opcodes.ADDLW,
				Opcodes.SUBLW,
				Opcodes.ANDLW,
				Opcodes.IORLW,
				Opcodes.XORLW
			):
				m.d.comb += result.eq(1)
			with m.Default():
				m.d.comb += result.eq(0)
		return result

	def storesWReg(self, m, opcode, dir):
		result = Signal(name = "storesWReg")
		with m.Switch(opcode):
			with m.Case(
				Opcodes.CLRW,
				Opcodes.MOVLW,
				Opcodes.RETLW,
				Opcodes.ADDLW,
				Opcodes.SUBLW,
				Opcodes.ANDLW,
				Opcodes.IORLW,
				Opcodes.XORLW
			):
				m.d.comb += result.eq(1)
			with m.Case(
				Opcodes.CLRF,
				Opcodes.DECF,
				Opcodes.DECFSZ,
				Opcodes.MOVF,
				Opcodes.COMF,
				Opcodes.INCF,
				Opcodes.INCFSZ,
				Opcodes.RRF,
				Opcodes.RLF,
				Opcodes.SWAPF,
				Opcodes.BCF,
				Opcodes.BSF
			):
				m.d.comb += result.eq(~dir)
			with m.Default():
				m.d.comb += result.eq(0)
		return result

	def storesFReg(self, m, opcode, dir):
		result = Signal(name = "storesFReg")
		with m.Switch(opcode):
			with m.Case(
				Opcodes.MOVWF,
				Opcodes.CLRF,
				Opcodes.SUBWF,
				Opcodes.DECF,
				Opcodes.DECFSZ,
				Opcodes.IORWF,
				Opcodes.ANDWF,
				Opcodes.XORWF,
				Opcodes.ADDWF,
				Opcodes.MOVF,
				Opcodes.COMF,
				Opcodes.INCF,
				Opcodes.INCFSZ,
				Opcodes.RRF,
				Opcodes.RLF,
				Opcodes.SWAPF
			):
				m.d.comb += result.eq(dir)
			with m.Case(
				Opcodes.BCF,
				Opcodes.BSF
			):
				m.d.comb += result.eq(1)
			with m.Default():
				m.d.comb += result.eq(0)
		return result

	def changesFlow(self, m, opcode):
		result = Signal(name = "changesFlow")
		with m.Switch(opcode):
			# Need to handle bit test f skip if <condition>..?
			with m.Case(
				Opcodes.CALL,
				Opcodes.GOTO,
				Opcodes.RETFIE,
				Opcodes.RETLW,
				Opcodes.RETURN
			):
				m.d.comb += result.eq(1)
			with m.Default():
				m.d.comb += result.eq(0)
		return result

	def isReturn(self, m, opcode):
		result = Signal(name = "isReturn")
		with m.Switch(opcode):
			with m.Case(
				Opcodes.RETFIE,
				Opcodes.RETLW,
				Opcodes.RETURN
			):
				m.d.comb += result.eq(1)
			with m.Default():
				m.d.comb += result.eq(0)
		return result

	def loadPCLatchHigh(self, m, opcode):
		result = Signal(name = "loadPCLatch")
		with m.Switch(opcode):
			with m.Case(
				Opcodes.CALL,
				Opcodes.GOTO
			):
				m.d.comb += result.eq(1)
			with m.Default():
				m.d.comb += result.eq(0)
		return result

	def storesZeroFlag(self, m, opcode):
		result = Signal(name = "storesZeroFlag")
		with m.Switch(opcode):
			with m.Case(
				Opcodes.CLRW,
				Opcodes.CLRF,
				Opcodes.SUBWF,
				Opcodes.DECF,
				Opcodes.IORWF,
				Opcodes.ANDWF,
				Opcodes.XORWF,
				Opcodes.ADDWF,
				Opcodes.MOVF,
				Opcodes.COMF,
				Opcodes.INCF,
				Opcodes.ADDLW,
				Opcodes.SUBLW,
				Opcodes.ANDLW,
				Opcodes.IORLW,
				Opcodes.XORLW
			):
				m.d.comb += result.eq(1)
			with m.Default():
				m.d.comb += result.eq(0)
		return result
