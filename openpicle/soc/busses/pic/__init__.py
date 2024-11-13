# SPDX-License-Identifier: BSD-3-Clause
from torii import Elaboratable, Module, Signal
from torii.build import Platform
from torii.util.units import log2_exact
from torii.lib.soc.memory import MemoryMap
from torii.lib.soc.csr.bus import Element as Register
from .types import Processor, Memory
from ....pic16 import PIC16
from typing import Optional, TYPE_CHECKING

__all__ = (
	'PICBus',
)

class PICBus(Elaboratable):
	def __init__(self) -> None:
		self.processor : Optional[PIC16] = None
		self.memoryMap = MemoryMap(addr_width = 7, data_width = 8)

	def add_processor(self, processor : PIC16):
		assert self.processor is None, "Cannot add more than one processor to the bus"
		self.processor = processor

	def add_register(self, *, address : int, access : Register.Access, name : str) -> Register:
		register = Register(width = self.memoryMap.data_width, access = access, name = name)
		self.memoryMap.add_resource(register, size = 1, addr = address, name = name)
		return register

	def add_memory(self, *, address : int, size : int) -> Memory:
		 # Validate size and create Memory instance..
		memory = Memory(address_width = log2_exact(size))
		self.memoryMap.add_resource(memory, size = size, addr = address, name = 'memory')
		return memory

	def elaborate(self, platform : Platform) -> Module:
		assert self.processor is not None, "Must provide a processor for PICBus to connect to"
		self.memoryMap.freeze()

		m = Module()
		processor = Processor()
		read = Signal()

		m.d.comb += self.processor.pBus.connect(processor)
		m.d.sync += read.eq(processor.read)

		for busResource in self.memoryMap.all_resources():
			addressBegin = busResource.start
			addressEnd = busResource.end
			dataWidth = busResource.width
			resource = busResource.resource
			if TYPE_CHECKING:
				assert isinstance(resource, (Register, Memory))
			assert dataWidth == 8
			addressCount = addressEnd - addressBegin
			addressSlice = log2_exact(addressCount)
			with m.If(processor.address[addressSlice:] == (addressBegin >> addressSlice)):
				if resource.access.readable():
					m.d.comb += [
						resource.r_stb.eq(read),
						processor.readData.eq(resource.r_data),
					]
				if resource.access.writable():
					m.d.comb += [
						resource.w_stb.eq(processor.write),
						resource.w_data.eq(processor.writeData),
					]
				if isinstance(resource, Memory):
					m.d.comb += resource.address.eq(processor.address[:addressSlice])

		return m
