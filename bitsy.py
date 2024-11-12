#!/usr/bin/env python3

from sys import argv, path
from pathlib import Path

gatewarePath = Path(argv[0]).resolve()
if (gatewarePath.parent / 'openpicle').is_dir():
		path.insert(0, str(gatewarePath.parent))

from torii import (
	Elaboratable, Module, Signal, Memory, Cat, Const, Instance,
	ClockDomain, ClockSignal, ResetSignal, DomainRenamer,
)
from torii.build import Resource, Pins, Attrs
from torii.util import tracer
from openpicle.soc.busses.pic import PICBus
from openpicle.pic16 import PIC16
from torii_boards.lattice.icebreaker_bitsy import ICEBreakerBitsyPlatform

class RAM(Elaboratable):
	def __init__(self, *, baseAddress, bus : PICBus):
		self._bus = bus.add_memory(address = baseAddress, size = 2 ** 3)
		self.contents = Memory(width = 8, depth = 2 ** 3)

	def elaborate(self, platform):
		m = Module()
		m.submodules.contents = memory = self.contents
		writePort = memory.write_port()
		readPort = memory.read_port(transparent = False)

		m.d.comb += [
			writePort.addr.eq(self._bus.address),
			writePort.data.eq(self._bus.writeData),
			writePort.en.eq(self._bus.write),

			readPort.addr.eq(self._bus.address),
			self._bus.readData.eq(readPort.data),
			readPort.en.eq(self._bus.read)
		]
		return m

class ROM(Elaboratable):
	def __init__(self):
		self.data = Signal(16)
		self.address = Signal(12)
		self.read = Signal()

		self.contents = Memory(width = 16, depth = 2 ** 12)

	def elaborate(self, platform):
		m = Module()
		m.submodules.contents = memory = self.contents
		writePort = memory.write_port()
		readPort = memory.read_port(transparent = False)

		m.d.comb += [
			writePort.addr.eq(0),
			writePort.data.eq(0),
			writePort.en.eq(0),

			readPort.addr.eq(self.address),
			self.data.eq(readPort.data),
			readPort.en.eq(self.read)
		]
		return m

class GPIO(Elaboratable):
	def __init__(self, *, baseAddress, bus : PICBus):
		namespace = tracer.get_var_name(depth = 2)
		self.inputs = Signal(8)
		self.outputs = Signal(8)
		self.outputEnables = Signal(8)

		self._registers = (
			bus.add_register(address = baseAddress, name = f'{namespace}.in'),
			bus.add_register(address = baseAddress + 1, name = f'{namespace}.out'),
			bus.add_register(address = baseAddress + 2, name = f'{namespace}.oe'),
		)
		self._baseAddress = baseAddress

	def next_address_after(self):
		return self._baseAddress + 3

	def elaborate(self, platform):
		m = Module()
		inputReg, outputReg, directionReg = self._registers
		inputs = self.inputs
		outputs = self.outputs
		directions = self.outputEnables

		with m.If(inputReg.read):
			m.d.comb += inputReg.readData.eq(inputs)

		with m.If(outputReg.read):
			m.d.comb += outputReg.readData.eq(outputs)
		with m.If(outputReg.write):
			m.d.sync += outputs.eq(outputReg.writeData)

		with m.If(directionReg.read):
			m.d.comb += directionReg.readData.eq(directions)
		with m.If(directionReg.write):
			m.d.sync += directions.eq(directionReg.writeData)
		return m

class Rebooter(Elaboratable):
	def __init__(self, *, sampleCounterWidth = 7, longCounterWidth = 17, buttonInverted = True):
		self.sampleCounterWidth = sampleCounterWidth
		self.longCounterWidth = longCounterWidth
		self.buttonInverted = buttonInverted

		# Inputs
		self.bootSelect = Signal()
		self.bootNow = Signal()
		self.buttonInput = Signal()

		# Outputs
		self.buttonValue = Signal()
		self.buttonPressed = Signal()
		self.willReboot = Signal()
		self.rebootTriggered = Signal()

	def elaborate(self, platform):
		m = Module()

		# Button sampling logic
		buttonCurrent = Signal()
		buttonInverted = 1 if self.buttonInverted else 0
		buttonValue = self.buttonValue
		buttonFalling = Signal()
		debounce = Signal(3)
		sampleCounterWidth = self.sampleCounterWidth + 1
		sampleCounter = Signal(sampleCounterWidth)
		sampleNow = Signal()

		_sampleCounterInc = Signal.like(sampleCounter)
		_sampleCounterMask = Signal.like(sampleCounter)
		_sampleCounterMaskBit = Signal()

		m.d.comb += [
			_sampleCounterInc.eq(Cat(sampleCounter[0:(sampleCounterWidth - 1)], 0) + 1),
			_sampleCounterMask.eq(_sampleCounterMaskBit.replicate(sampleCounterWidth)),
			_sampleCounterMaskBit.eq(~sampleCounter[sampleCounterWidth - 1]),
			sampleNow.eq(sampleCounter[sampleCounterWidth - 1]),
			buttonValue.eq(debounce[2]),
		]

		m.d.sync += [
			buttonCurrent.eq(self.buttonInput ^ buttonInverted),
			# This takes the top bit of the counter, inverts and replicates it, and ands that with
			# The rest of the counter incremented by 1, which creates a self-resetting counter
			sampleCounter.eq(_sampleCounterInc & _sampleCounterMask),
			buttonFalling.eq((debounce == 0b100) & ~buttonCurrent & sampleNow),
		]

		with m.If(sampleNow):
			with m.Switch(Cat(buttonCurrent, debounce)):
				with m.Case('0--0'):
					m.d.sync += debounce.eq(0b000)
				with m.Case('0001'):
					m.d.sync += debounce.eq(0b001)
				with m.Case('0011'):
					m.d.sync += debounce.eq(0b010)
				with m.Case('0101'):
					m.d.sync += debounce.eq(0b011)
				with m.Case('0111', '1--1'):
					m.d.sync += debounce.eq(0b111)
				with m.Case('1110'):
					m.d.sync += debounce.eq(0b110)
				with m.Case('1100'):
					m.d.sync += debounce.eq(0b101)
				with m.Case('1010'):
					m.d.sync += debounce.eq(0b100)
				with m.Case('1000'):
					m.d.sync += debounce.eq(0b000)
				with m.Default():
					m.d.sync += debounce.eq(0b000)

		# Long-press and Arming logic
		armed = Signal()
		longCounterWidth = self.longCounterWidth + 1
		longCounter = Signal(longCounterWidth)

		_longCounterInc = Signal.like(longCounter)
		_longCounterMask = Signal.like(longCounter)
		_longCounterMaskBit = Signal()

		m.d.comb += [
			_longCounterInc.eq(longCounter + Cat(~longCounter[longCounterWidth - 1], Const(0).replicate(longCounterWidth - 1))),
			_longCounterMask.eq(_longCounterMaskBit.replicate(longCounterWidth)),
			_longCounterMaskBit.eq(~(armed ^ buttonValue)),
		]

		m.d.sync += [
			armed.eq(armed | longCounter[longCounterWidth - 3]),
			longCounter.eq(_longCounterInc & _longCounterMask),
		]

		# Command logic
		warmbootSelect = Signal(2)
		warmbootRequest = Signal()
		willReboot = self.willReboot

		m.d.comb += willReboot.eq(armed & longCounter[longCounterWidth - 1])

		with m.If(~warmbootRequest):
			with m.If(self.bootNow):
				m.d.sync += [
					warmbootSelect.eq(self.bootSelect),
					warmbootRequest.eq(1),
					self.buttonPressed.eq(0),
				]
			with m.Else():
				m.d.sync += [
					warmbootSelect.eq(0b01),
					warmbootRequest.eq((willReboot & buttonFalling) | warmbootRequest),
					self.buttonPressed.eq(armed & buttonFalling & ~longCounter[longCounterWidth - 1]),
				]

		# Rebooter
		warmbootNow = Signal()
		m.d.sync += warmbootNow.eq(warmbootRequest)
		m.d.comb += self.rebootTriggered.eq(warmbootNow)

		# This is not generated when this elaboratable is sim'd.
		if platform is not None:
			m.submodules += Instance(
				'SB_WARMBOOT',
				i_BOOT = warmbootNow,
				i_S0 = warmbootSelect[0],
				i_S1 = warmbootSelect[1],
			)

		return m

pmods = [
	Resource('pmod', 1,
		Pins('1 3 5 7 2 4 6 8', dir='io', conn=('edge', 0)), Attrs(IO_STANDARD = 'SB_LVCMOS'),
	)
]

class IOWO(Elaboratable):
	program = [ # This program starts at address 0
		0x3064, # MOVLW     100
		0x0090, # MOVWF     0x10
		0x0091, # MOVWF     0x11
		0x0092, # MOVWF     0x12 - This should be address 3

		0x3001, # MOVLW     0x01
		0x0681, # XORWF     0x01,f - Toggles the red LED on/off

		0x3064, # MOVLW     100
		0x0B90, # DECFSZ    0x10,f - This should be address 7
		0x2807, # GOTO      0x007
		0x0090, # MOVWF     0x10 - Reload the counter
		0x0B91, # DECFSZ    0x11,f
		0x2807, # GOTO      0x007
		0x0091, # MOVWF     0x11 - Reload the counter
		0x0B92, # DECFSZ    0x12,f
		0x2807, # GOTO      0x007
		0x2803, # GOTO      0x003 - Once we've gone through 100*100*100 iterations,
				#                   jump back to the instruction that reloads the last counter
	]

	def __init__(self, *, sim = False):
		if sim:
			self.ledR = Signal()
			self.ledG = Signal()
			self.userBtn = Signal()

			self.address = Signal(12)
			self.data = Signal(16)
			self.read = Signal()

	def elaborate(self, platform):
		m = Module()
		m.domains.processor = ClockDomain()
		m.submodules.bus = pBus = PICBus()
		m.submodules.processor = processor = DomainRenamer({'sync': 'processor'})(PIC16())
		# This is not generated when this elaboratable is sim'd.
		if platform is not None:
			m.submodules.rom = rom = ROM()
		m.submodules.rebooter = rebooter = Rebooter(longCounterWidth = 23, buttonInverted = False)

		iBus = processor.iBus

		# This is not generated when this elaboratable is sim'd.
		if platform is not None:
			rom.contents.init = IOWO.program

			m.d.comb += [
				rom.address.eq(iBus.address),
				iBus.data.eq(rom.data),
				rom.read.eq(iBus.read),
			]
		else:
			m.d.comb += [
				self.address.eq(iBus.address),
				iBus.data.eq(self.data),
				self.read.eq(iBus.read),
			]

		baseAddress = 0x0
		pBus.add_processor(processor)
		m.submodules.gpioA = gpioA = GPIO(baseAddress = baseAddress, bus = pBus)
		baseAddress = gpioA.next_address_after()
		m.submodules.gpioB = gpioB = GPIO(baseAddress = baseAddress, bus = pBus)
		baseAddress = gpioB.next_address_after()
		m.submodules.ram = RAM(baseAddress = 0x10, bus = pBus)

		ready = Signal(range(3))

		m.d.sync += ready.eq(ready + ~ready[1])
		m.d.comb += [
			ClockSignal('processor').eq(ClockSignal()),
			ResetSignal('processor').eq(~ready[1])
		]

		# This is not generated when this elaboratable is sim'd.
		if platform is not None:
			ledR = platform.request('led_r')
			m.d.comb += [
				ledR.o.eq(gpioA.outputs[0])
			]

			ledG = platform.request('led_g')
			userBtn = platform.request('button', 0)
			m.d.comb += [
				rebooter.buttonInput.eq(userBtn),
				ledG.eq(rebooter.willReboot)
			]

			pmod1 = platform.request('pmod', 1)
			m.d.comb += [
				gpioB.inputs.eq(pmod1.i),
				pmod1.o.eq(gpioB.outputs),
				pmod1.oe.eq(gpioB.outputEnables)
			]
		else:
			m.d.comb += [
				self.ledR.eq(gpioA.outputs[0]),
				rebooter.buttonInput.eq(self.userBtn),
				self.ledG.eq(rebooter.willReboot),
			]
		return m

if __name__ == '__main__':
	#from torii.build import Clock
	platform = ICEBreakerBitsyPlatform()
	#platform.resources['clk12', 0].clock = Clock(48e6)
	platform.add_resources(pmods)
	platform.build(IOWO(), name = "bitsy", do_program = True,
		synth_opts = ['-abc9'], nextpnr_opts = ['--tmg-ripup', '--seed=0', '--write', 'bitsy.pnr.json'],
	)
