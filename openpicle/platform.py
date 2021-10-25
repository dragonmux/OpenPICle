# SPDX-License-Identifier: BSD-3-Clause
from nmigen.vendor.openlane import OpenLANEPlatform
from nmigen_boards.resources.memory import SPIFlashResources

__all__ = (
	'OpenPIClePlatform',
)

class OpenPIClePlatform(OpenLANEPlatform):
	pdk = 'sky130A'
	cell_library = 'sky130_fd_sc_hs'

	settings = {
		"PL_TARGET_DENSITY": 0.75,
		#"FP_HORIZONTAL_HALO": 6,
		#"FP_VERTICAL_HALO": 6,
		"FP_CORE_UTIL": 25,
		"DIODE_INSERTION_STRATEGY": 4,
	}

	resources = [
		*SPIFlashResources(0,
			cs_n = 'qspi_cs',
			clk = 'qspi_clk',
			copi = 'qspi_io0',
			cipo = 'qspi_io1',
			wp_n = 'qspi_io2',
			hold_n = 'qspi_io3'
		)
	]

	connectors = []

	def build(self, elaboratable, build_dir = 'build', do_build = True,
		program_opts = None, do_program = False, **kwargs
	):
		return super().build(elaboratable, name = 'user_project_wrapper', build_dir = build_dir,
			do_build = do_build, program_opts = program_opts, do_program = do_program,
			ports = elaboratable.get_ports(), **kwargs)
