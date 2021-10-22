# SPDX-License-Identifier: BSD-3-Clause
from nmigen import Elaboratable, tracer
from nmigen_soc import csr
from nmigen_soc.memory import MemoryMap

__all__ = ['Peripheral', 'CSRBank', 'PeripheralBridge']

class Peripheral(object):
	Interface = None

	def __init__(self, name = None, src_loc_at = 1):
		if name is not None and not isinstance(name, str):
			raise TypeError('Name must be a string, not {!r}'.format(name))
		self.name = name or tracer.get_var_name(depth = 2 + src_loc_at).lstrip('_')

		self._csr_banks = []
		self._windows = []

		self._bus = None

	@property
	def bus(self):
		if self._bus is None:
			raise NotImplementedError('Peripheral {!r} does not have a bus interface'.format(self))
		return self._bus

	@bus.setter
	def bus(self, bus):
		self._bus = bus

	def csr_bank(self, *, addr = None, alignment = None, desc = None):
		bank = CSRBank(name_prefix = self.name)
		self._csr_banks.append((bank, addr, alignment))
		return bank

	def window(self, *, addr_width, data_width, granularity = None, features = frozenset(),
		alignment = 0, addr = None, sparse = None):
		window = self.Interface(addr_width = addr_width, data_width = data_width,
			granularity = granularity, features = features)
		granularityBits = log2Int(data_width // window.granularity)
		window.memory_map = MemoryMap(addr_width = addr_width + granularityBits,
			data_width = window.granularity, alignment = alignment)
		self._windows.append((window, addr, sparse))
		return window

	def bridge(self, *, data_width = 0, granularity = None, features = frozenset(), alignment = 0):
		return PeripheralBridge(self, data_width = data_width, granularity = granularity,
			features = features, alignment = alignment)

	def iter_csr_banks(self):
		for (bank, addr, alignment) in self._csr_banks:
			yield (bank, addr, alignment)

	def iter_windows(self):
		for (window, addr, sparse) in self._windows:
			yield (window, addr, sparse)

class CSRBank(object):
	def __init__(self, *, name_prefix = ''):
		self._name_prefix = name_prefix
		self._csr_regs = []

	def csr(self, width, access, *, addr = None, alignment = None, name = None, desc = None, src_loc_at = 0):
		if name is not None and not isinstance(name, str):
			raise TypeError('Name must be a string, not {!r}'.format(name))
		name = name or tracer.get_var_name(depth = 2 + src_loc_at).lstrip('_')

		elem_name = '{}_{}'.format(self._name_prefix, name)
		elem = csr.Element(width, access, name = elem_name)
		self._csr_regs.append((elem, addr, alignment))
		return elem

	def iter_csr_regs(self):
		for (elem, addr, alignment) in self._csr_regs:
			yield (elem, addr, alignment)

class PeripheralBridge(Elaboratable):
	pass
