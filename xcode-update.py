#!/usr/bin/env python3
"""
Script to update Xcode automatically.

This is a wrapper around `xcodes` (https://github.com/RobotsAndPencils/xcodes).
"""

import sys
from shutil import which
import argparse
import subprocess


def parse_args():
	"""Parse the Command Line arguments and generate the Command Line help."""

	root_parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)  # Uses file's default docstring
	# Arguments
	root_parser.add_argument('-v', '--version', action='version', version='1.0.0')
	root_parser.add_argument('-r', '--release', type=int, default=1, help='The number of Xcode release versions to preserve. By default, only 1 release version is preserved')
	root_parser.add_argument('-b', '--betas', type=int, default=1, help='The number of Xcode beta versions to preserve. By default, only 1 beta version is preserved')
	return root_parser.parse_args()


def main():
	if not sys.platform == 'darwin':
		raise NotImplementedError("This program only works on macOS")
	if which("xcodes") is None:
		raise AssertionError("xcodes isn't installed. You must install xcodes from https://github.com/RobotsAndPencils/xcodes")
	if which("aria2c") is None:
		print("WARNING: aria2 is not installed. This makes downloading Xcode versions significantly slower. You can install it with `brew install aria2`.")

	args = parse_args()
	if args.release < 1 or args.betas < 1:
		raise AssertionError("Invalid value of Xcode versions to preserve (it must be more than 1)")
	install_latest_xcode_versions()
	delete_unnecessary_xcode_versions(args.release, args.betas)
	
	
def install_latest_xcode_versions():
	"""Install the latest Xcode versions, if they aren't already installed."""
	
	subprocess.run(['xcodes', 'install', '--latest'], check=True)
	subprocess.run(['xcodes', 'install', '--latest-prerelease'], check=True)
	

def delete_unnecessary_xcode_versions(number_release: int, number_betas: int):
	"""Deletes old Xcode versions."""

	installed_versions = subprocess.run(['xcodes', 'installed'], check=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
	print("Deletion of Xcode versions is not implemented yet")
	# TODO: Distinguish between release and beta versions
	# TODO: Actually delete Xcode versions


if __name__ == '__main__':
	sys.tracebacklimit = 0
	sys.exit(main())
