# SPDX-License-Identifier: BSD-3-Clause
from amaranth.vendor.openlane import Sky130HighSpeedPlatform
from amaranth import Module, Signal
from amaranth.build import Resource, Pins, Clock, Attrs
from amaranth_boards.resources.memory import SPIFlashResources
from pathlib import Path
from jinja2.filters import do_mark_safe as safe

__all__ = (
	'OpenPIClePlatform',
)

class OpenPIClePlatform(Sky130HighSpeedPlatform):
	#pdk = 'sky130B'

	default_clk = 'clk'
	default_rst = 'rst'

	unit = 2.4

	flow_settings = {
		# "PL_TARGET_DENSITY": 0.75,
		# Caravel specific area config
		"MAGIC_ZEROIZE_ORIGIN": 0,
		"FP_SIZING": "absolute",
		# Caravel provides 2920x3520µm for activites
		"DIE_AREA": "0 0 2920 3520",
		"DIODE_INSERTION_STRATEGY": 0,
		# We copied their pin order file as we have to match it.
		"FP_PIN_ORDER_CFG": "/design_user_project_wrapper/pinOrder.cfg",
		# Caravel requires we use the following floorplanning settings:
		"FP_IO_VEXTEND": 2 * unit,
		"FP_IO_VLENGTH": unit,
		"FP_IO_VTHICKNESS_MULT": 4,
		"FP_IO_HEXTEND": 2 * unit,
		"FP_IO_HLENGTH": unit,
		"FP_IO_HTHICKNESS_MULT": 4,
		# Caravel requries we use the following PDN settings:
		"FP_PDN_CORE_RING": 1,
		"FP_PDN_CORE_RING_VWIDTH": 3.1,
		"FP_PDN_CORE_RING_VOFFSET": 14,
		"FP_PDN_CORE_RING_VSPACING": 1.7,
		"FP_PDN_CORE_RING_HWIDTH": 3.1,
		"FP_PDN_CORE_RING_HOFFSET": 14,
		"FP_PDN_CORE_RING_HSPACING": 1.7,
		"FP_PDN_VWIDTH": 3.1,
		"FP_PDN_VSPACING": safe("[expr 5*$::env(FP_PDN_CORE_RING_VWIDTH)]"),
		"FP_PDN_HWIDTH": 3.1,
		"FP_PDN_HSPACING": safe("[expr 5*$::env(FP_PDN_CORE_RING_HWIDTH)]"),
		"FP_PDN_CHECK_NODES": 0,
		"GLB_RT_OBS": safe('"{}"'.format(", ".join((
			"met1 0 0 $::env(DIE_AREA)",
			"met2 0 0 $::env(DIE_AREA)",
			"met3 0 0 $::env(DIE_AREA)",
			"met4 0 0 $::env(DIE_AREA)",
			"met5 0 0 $::env(DIE_AREA)",
		)))),
		# User-configurable PDN settings:
		"FP_PDN_VPITCH": 180,
		"FP_PDN_VOFFSET": 5,
		"FP_PDN_HPITCH": safe("$::env(FP_PDN_VPITCH)"),
		"FP_PDN_HOFFSET": safe("$::env(FP_PDN_VOFFSET)"),
		# Caravel-required power nets:
		"VDD_NETS": safe("[list {vccd1} {vccd2} {vdda1} {vdda2}]"),
		"GND_NETS": safe("[list {vssd1} {vssd2} {vssa1} {vssa2}]"),
		"SYNTH_USE_PG_PINS_DEFINES": "USE_POWER_PINS",
		# Passes/phases/opts that Caravel turns off:
		"PL_OPENPHYSYN_OPTIMIZATIONS": 0,
		# Caravel turns this off??
		"RUN_CVC": 0,
		"MAGIC_WRITE_FULL_LEF": 0,
	}

	resources = [
		Resource('clk', 0, Pins('io_15', dir = 'i', assert_width = 1),
			Clock(100e6), Attrs()
		),

		Resource('rst', 0, Pins('io_16', dir = 'i', assert_width = 1),
			Attrs()
		),

		*SPIFlashResources(0,
			cs_n = 'io_0',
			clk = 'io_4',
			copi = 'io_3',
			cipo = 'io_1',
			wp_n = 'io_2',
			hold_n = 'io_6'
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
				Signal(name = f'vccd{i + 1}'),
				Signal(name = f'vdda{i + 1}'),
				Signal(name = f'vssd{i + 1}'),
				Signal(name = f'vssa{i + 1}'),
			])

		return super().build(elaboratable, name = 'user_project_wrapper', build_dir = build_dir,
			do_build = do_build, program_opts = program_opts, do_program = do_program,
			ports = ports, **kwargs)

	def prepare(self, elaboratable, name, **kwargs):
		def add_file(self, filePath : Path):
			assert filePath.exists()
			print(filePath.name)
			with open(f'{filePath}', 'rb') as file:
				self.add_file(filePath.name, file)

		add_file(self, Path(__file__).resolve().parent / 'pinOrder.cfg')
		add_file(self, Path(__file__).resolve().parent / 'interactive.tcl')
		add_file(self, Path(__file__).resolve().parent / 'pdn.tcl')
		add_file(self, Path(__file__).resolve().parent / 'gen_pdn.tcl')
		plan = super().prepare(elaboratable, name, **kwargs)
		return plan

	def _pin_to_res(self, search_pin):
		for res, pin, port, attrs in self._ports:
			if pin is search_pin:
				return res
		raise LookupError()

	def _get_io(self, pin, port, invert):
		m = Module()
		resource = self._pin_to_res(pin)
		phys_names = resource.ios[0].names
		ios = []
		for phys in phys_names:
			name, index = phys.rsplit('_', 1)
			if 'i' in pin.dir:
				pin_i = Signal(name = f'{name}_in[{index}]')
				m.d.comb += pin.i.eq(~pin_i if invert else pin_i)
				ios.append(pin_i)
			if 'o' in pin.dir:
				pin_o = Signal(name = f'{name}_out[{index}]')
				m.d.comb += pin_o.eq(~pin.o if invert else pin.o)
				ios.append(pin_o)
			if pin.dir in ('oe', 'io'):
				pin_oe = Signal(name = f'{name}_oeb[{index}]')
				m.d.comb += pin_oe.eq(~pin.oe)
				ios.append(pin_oe)
		port.io = ios
		return m

	def get_input(self, pin, port, attrs, invert):
		return self._get_io(pin, port, invert)

	def get_output(self, pin, port, attrs, invert):
		return self._get_io(pin, port, invert)

	def get_tristate(self, pin, port, attrs, invert):
		return self._get_io(pin, port, invert)

	def get_input_output(self, pin, port, attrs, invert):
		return self._get_io(pin, port, invert)
