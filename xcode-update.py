#!/usr/bin/env python3
"""
Script to update Xcode automatically.

This is a wrapper around `xcodes` (https://github.com/RobotsAndPencils/xcodes).
"""

import sys
from shutil import which
import argparse
import subprocess
from pathlib import Path


# Symlink to the latest Xcode release version.
XCODE_RELEASE = Path(f'/Applications/Xcode.app')
# Symlink to the latest Xcode prerelease version.
XCODE_BETA = Path(f'/Applications/Xcode-beta.app')
# String that Xcodes adds to a version to indicate it's already installed. Note the space at the beginning.
XCODES_INSTALLED_MAGIC_STRING = ' (Installed)'
# String that Xcodes adds to a version to indicate it's a Beta version.
XCODES_BETA_MAGIC_STRING = 'Beta'

def parse_args():
	"""Parse the Command Line arguments and generate the Command Line help."""

	root_parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)  # Uses file's default docstring
	# Arguments
	root_parser.add_argument('-v', '--version', action='version', version='1.0.0')
	root_parser.add_argument('-n', '--non-interactive', action='store_false', dest='interactive', help='Installs and deletes Xcode versions without asking for permission first')
	return root_parser.parse_args()


def main():
	if not sys.platform == 'darwin':
		raise NotImplementedError("This program only works on macOS")
	if which("xcodes") is None:
		raise AssertionError("xcodes isn't installed. You must install xcodes from https://github.com/RobotsAndPencils/xcodes")
	if which("aria2c") is None:
		print("WARNING: aria2 is not installed. This makes downloading Xcode versions significantly slower. You can install it with `brew install aria2`.")

	args = parse_args()
	if args.interactive:
		install_latest_xcode(dry_run=True)
		update_symlinks(dry_run=True)
		delete_xcode(dry_run=True)
		ask_for_confirmation("Continue updating? (Y/n): ")
	install_latest_xcode(dry_run=False)
	update_symlinks(dry_run=False)
	delete_xcode(dry_run=False)
	
	
def install_latest_xcode(dry_run: bool):
	"""Install the latest Xcode version, if it isn't already installed."""
	
	latest_version = latest_xcode_version()
	if XCODES_INSTALLED_MAGIC_STRING in latest_version:
		latest_version = latest_version.replace(XCODES_INSTALLED_MAGIC_STRING, '')
		print(f'{latest_version} is already installed. Nothing to do.')
		exit()
	print(f'- Xcode version {latest_version} will be installed.')
	
	if not dry_run:
		print("Installation of Xcode versions is not implemented yet")
		#subprocess.run(['xcodes', 'install', '--latest-prerelease'], check=True)


def update_symlinks(dry_run: bool):
	"""Updates the symlinks to the latest Xcode version."""

	latest_version = latest_xcode_version()
	current_beta = None
	if not XCODE_BETA.exists():
		print(f'- {XCODE_BETA} will be created pointing to Xcode {latest_version}.')
	else:
		current_beta = XCODE_BETA.resolve()
		print(f'- {XCODE_BETA} will stop linking to {current_beta} and start pointing to Xcode {latest_version}.')
	# Xcode release versions are only updated when the current beta (that's about to be replaced) points to a release version
	if is_release_version(current_beta):
		if not XCODE_RELEASE.exists():
			print(f'- {XCODE_RELEASE} will be created pointing to {current_beta}.')
		else:
			current_release = XCODE_RELEASE.resolve()
			print(f'- {XCODE_RELEASE} will stop linking to {current_release} and start pointing to {current_beta}.')

	if not dry_run:
		print("The update of the symlinks is not implemented yet")


def delete_xcode(dry_run: bool):
	"""Deletes the oldest Xcode version."""

	# Xcode release versions are only updated when the current beta (that's about to be replaced) points to a release version
	current_beta = XCODE_BETA.resolve()
	should_delete_release_version = is_release_version(current_beta)
	xcode_version_to_delete = oldest_xcode_version(include_releases=should_delete_release_version)
	if xcode_version_to_delete:
		print(f'- {xcode_version_to_delete} will be deleted.')
	
	if not dry_run:
		print(f'Deleting {str(xcode_version_to_delete)}...')
		print("Deletion of Xcode versions is not implemented yet")
		
		
def ask_for_confirmation(prompt: str):
	"""Shows the prompt and waits for the user to answer. If the user answer "No", the program is halted."""
	
	answer = None
	while answer not in ('y', 'n', ''): # '' = "Enter" key, by default we let the script continue
		answer = input(prompt)
		if answer: # If the answer is the enter key, the string is empty
			answer = answer[0].lower()
	if answer == 'n':
		exit()
	
	
def latest_xcode_version() -> str:
	"""Returns the latest Xcode version available"""
	
	all_versions = subprocess.run(['xcodes', 'list'], check=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
	return all_versions.split("\n")[-2] # The last string (-1 on the array) is always empty
	
	
def is_release_version(path: Path) -> bool:
	"""Verifies if the supplied Xcode version is a Release version"""
	
	if path is None:
		return False
	installed_versions = subprocess.run(['xcodes', 'installed'], check=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
	for version in installed_versions.split("\n"):
		if str(path) in version:
			return not XCODES_BETA_MAGIC_STRING in version
	AssertionError(f"{path} doesn't seems to be a valid Xcode version")
	
	
def oldest_xcode_version(include_releases: bool) -> Path:
	"""Returns the path to the oldest Xcode version, to be able to delete it.
	The parameter allows to only delete beta versions (to keep a release version even if it's older)."""
	
	installed_versions = subprocess.run(['xcodes', 'installed'], check=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
	for version in installed_versions.split("\n"):
		if include_releases | (XCODES_BETA_MAGIC_STRING in version):
			return version.split("\t")[1]
	return None # There could be no previous Xcode versions


if __name__ == '__main__':
	sys.tracebacklimit = 0 # Disables Python's Traceback, to show clearer errors.
	sys.exit(main())
