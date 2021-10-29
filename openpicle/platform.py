# SPDX-License-Identifier: BSD-3-Clause
from nmigen.vendor.openlane import OpenLANEPlatform
from nmigen import Signal
from nmigen.build import Resource, Pins, Clock, Attrs
from nmigen_boards.resources.memory import SPIFlashResources

__all__ = (
	'OpenPIClePlatform',
)

class OpenPIClePlatform(OpenLANEPlatform):
	pdk = 'sky130A'
	cell_library = 'sky130_fd_sc_hs'

	default_clk = 'clk'
	default_rst = 'rst'

	unit = 2.4

	flow_settings = {
		"PL_TARGET_DENSITY": 0.75,
		#"FP_HORIZONTAL_HALO": 6,
		#"FP_VERTICAL_HALO": 6,
		"FP_CORE_UTIL": 10,
		# Caravel provides 2920x3520µm for activites
		"DIE_AREA": "0 0 2920 3520",
		"DIODE_INSERTION_STRATEGY": 4,
		# We copied their pin order file as we have to match it.
		"FP_PIN_ORDER_CFG": "/design_user_project_wrapper/pinOrder.cfg",
		# Caravel requires we use the following floorplanning settings:
		"FP_IO_VEXTEND": 2 * unit,
		"FP_IO_VLENGTH": unit,
		"FP_IO_VTHICKNESS_MULT": 4,
		"FP_IO_HEXTEND": 2 * unit,
		"FP_IO_HLENGTH": unit,
		"FP_IO_HTHICKNESS_MULT": 4,
		"GLB_RT_OBS": r"""
			met1 0 0 $::env(DIE_AREA),\
			met2 0 0 $::env(DIE_AREA),\
			met3 0 0 $::env(DIE_AREA),\
			met4 0 0 $::env(DIE_AREA),\
			met5 0 0 $::env(DIE_AREA)\
		""",
		# Caravel-required power nets:
		"VDD_NETS": "[list {vccd1} {vccd2} {vdda1} {vdda2}]",
		"GND_NETS": "[list {vssd1} {vssd2} {vssa1} {vssa2}]",
		"SYNTH_USE_PG_PINS_DEFINES": "USE_POWER_PINS",
		# Passes/phases/opts that Caravel turns off:
		"PL_OPENPHYSYN_OPTIMIZATIONS": 0,
		# Caravel turns this off??
		"RUN_CVC": 0,
		"MAGIC_WRITE_FULL_LEF": 0,
	}

	resources = [
		Resource('clk', 0, Pins('clk', dir = 'i', assert_width = 1),
			Clock(100e6), Attrs()
		),

		Resource('rst', 0, Pins('rst', dir = 'i', assert_width = 1),
			Attrs()
		),

		*SPIFlashResources(0,
			cs_n = 'qspi_cs',
			clk = 'qspi_clk',
			copi = 'qspi_io0',
			cipo = 'qspi_io1',
			wp_n = 'qspi_io2',
			hold_n = 'qspi_io3'
		),
	]

	connectors = []

	def build(self, elaboratable, build_dir = 'build', do_build = True,
		program_opts = None, do_program = False, **kwargs
	):
		ports = elaboratable.get_ports()
		# This generates the power nets for the top-level even though we do nothing with them
		for i in range(2):
			ports.extend([
				Signal(name = f'vccd{i}'),
				Signal(name = f'vdda{i}'),
				Signal(name = f'vssd{i}'),
				Signal(name = f'vssa{i}'),
			])

		return super().build(elaboratable, name = 'user_project_wrapper', build_dir = build_dir,
			do_build = do_build, program_opts = program_opts, do_program = do_program,
			ports = ports, **kwargs)

	def prepare(self, elaboratable, name, **kwargs):
		plan = super().prepare(elaboratable, name, **kwargs)
		pinFile = Path(__file__).resolve().parent / 'pinOrder.cfg'
		assert pinFile.exists()
		with open(f'{pinFile}', 'rb') as file:
			plan.add_file('pinOrder.cfg', file.read())
		return plan
