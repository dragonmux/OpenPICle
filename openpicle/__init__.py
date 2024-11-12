# SPDX-License-Identifier: BSD-3-Clause
from .platform import OpenPIClePlatform
from .caravel import PIC16Caravel

__all__ = (
	'cli',
)

def cli():
	from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

	# Build the command line parser
	parser = ArgumentParser(formatter_class = ArgumentDefaultsHelpFormatter,
		description = 'OpenPICle')
	parser.add_argument('--verbose', '-v', action = 'store_true', help = 'Enable debugging output')

	# Create action subparsers for building and simulation
	actions = parser.add_subparsers(dest = 'action', required = True)
	actions.add_parser('build', help = 'build OpenPICle for OpenLane')
	actions.add_parser('sim', help = 'Simulate and test the gateware components')

	# Parse the command line and, if `-v` is specified, bump the logging level
	args = parser.parse_args()
	if args.verbose:
		from logging import root, DEBUG
		root.setLevel(DEBUG)

	# Dispatch the action requested
	if args.action == 'sim':
		from unittest.loader import TestLoader
		from unittest.runner import TextTestRunner

		loader = TestLoader()
		tests = loader.discover(start_dir = 'openpicle.sim', pattern = '*.py')

		runner = TextTestRunner()
		runner.run(tests)
		return 0
	elif args.action == 'build':
		platform = OpenPIClePlatform()
		platform.build(PIC16Caravel())
		return 0
