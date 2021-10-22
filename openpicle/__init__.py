# SPDX-License-Identifier: BSD-3-Clause
#from nmigen.vendor.openlane

def cli():
	from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
	from arachne.cli import register_cli

	parser = ArgumentParser(formatter_class = ArgumentDefaultsHelpFormatter,
		description = 'OpenPICle')
	actions = parser.add_subparsers(dest = 'action', required = True)
	actions.add_parser('build', help = 'build OpenPICle for OpenLane')

	register_cli(parser = parser)
	args = parser.parse_args()

	if args.action == 'arachne-sim':
		from arachne.core.sim import run_sims
		run_sims(pkg = 'openpicle/sim', result_dir = 'build')
		return 0
