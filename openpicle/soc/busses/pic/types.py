# SPDX-License-Identifier: BSD-3-Clause
from torii import Record
from torii.hdl.rec import Direction
from torii.lib.soc.csr.bus import Element

__all__ = ('Processor', 'Memory')

class Processor(Record):
	def __init__(self, *, name = None):
		layout = [
			("address", 7, Direction.FANOUT),
			("read", 1, Direction.FANOUT),
			("readData", 8, Direction.FANIN),
			("write", 1, Direction.FANOUT),
			("writeData", 8, Direction.FANOUT),
		]

		super().__init__(layout, name = name, src_loc_at = 1)

class Memory(Record):
	access = Element.Access.RW

	def __init__(self, *, address_width, name = None):
		layout = [
			("address", address_width, Direction.FANIN),
			("r_stb", 1, Direction.FANIN),
			("r_data", 8, Direction.FANOUT),
			("w_stb", 1, Direction.FANIN),
			("w_data", 8, Direction.FANIN),
		]

		super().__init__(layout, name = name, src_loc_at = 1)
