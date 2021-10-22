# SPDX-License-Identifier: BSD-3-Clause
from nmigen import Record
from ..soc.busses.pic.types import Processor as PeripheralBus

__all__ = ('InstructionBus', 'PeripheralBus')

class InstructionBus(Record):
	def __init__(self, *, name = None):
		layout = [
			("address", 12),
			("data", 14),
			("read", 1),
		]

		super().__init__(layout, name = name, src_loc_at = 1)
