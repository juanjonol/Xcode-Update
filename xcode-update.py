#!/usr/bin/env python3
"""
Script to update Xcode automatically.

This is a wrapper around `xcodes` (https://github.com/RobotsAndPencils/xcodes).
"""

import sys
import shutil
import argparse
import subprocess
from pathlib import Path
import os


# Link to the latest Xcode release version.
XCODE_RELEASE = Path(f'/Applications/Xcode.app')
# Link to the latest Xcode prerelease version.
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
	root_parser.add_argument('-s', '--skip-delete', action='store_false', dest='delete', help="Don't delete the oldest Xcode version")
	return root_parser.parse_args()


def main():
	if not sys.platform == 'darwin':
		raise NotImplementedError("This program only works on macOS")
	if shutil.which("xcodes") is None:
		raise AssertionError("xcodes isn't installed. You must install xcodes from https://github.com/RobotsAndPencils/xcodes")
	if shutil.which("aria2c") is None:
		print("WARNING: aria2 is not installed. This makes downloading Xcode versions significantly slower. You can install it with `brew install aria2`.")

	args = parse_args()
	verify_permissions()
	if args.interactive:
		install_latest_xcode(dry_run=True)
		if args.delete:
			delete_xcode(dry_run=True)
		update_links(dry_run=True)
		ask_for_confirmation("Continue updating? (Y/n): ")
	install_latest_xcode(dry_run=False)
	if args.delete:
		delete_xcode(dry_run=False)
	update_links(dry_run=False)
	
	
def verify_permissions():
	"""Verify that the current user has write access to Xcode's directory."""
	
	xcode_directory = os.environ['XCODES_DIRECTORY']
	if not xcode_directory:
		xcode_directory = '/Applications'
	if not os.access(xcode_directory, os.R_OK | os.W_OK):
		raise PermissionError(f"The current user doesn't have permissions to install Xcode on {xcode_directory}")
	
	
def install_latest_xcode(dry_run: bool):
	"""Install the latest Xcode version, if it isn't already installed."""
	
	latest_version = latest_xcode_version()
	if XCODES_INSTALLED_MAGIC_STRING in latest_version:
		latest_version = latest_version.replace(XCODES_INSTALLED_MAGIC_STRING, '')
		print(f'{latest_version} is already installed. Nothing to do.')
		exit()
	print(f'- Xcode version {latest_version} will be installed.')
	
	if not dry_run:
		subprocess.run(['xcodes', 'install', f'{latest_version}'], check=True)


def delete_xcode(dry_run: bool):
	"""Deletes the oldest Xcode version."""

	# Xcode release versions are only updated when the current beta (that's about to be replaced) points to a release version
	current_beta = XCODE_BETA.resolve()
	should_delete_release_version = is_release_version(current_beta)
	xcode_version_to_delete = oldest_xcode_version(include_releases=should_delete_release_version)
	if xcode_version_to_delete:
		print(f'- {xcode_version_to_delete} will be deleted.')
	
	if not dry_run:
		shutil.rmtree(str(xcode_version_to_delete))
		
		
def update_links(dry_run: bool):
	"""Updates the links to the latest Xcode version."""

	latest_version = latest_xcode_version()
	current_beta = None
	if not XCODE_BETA.exists():
		print(f'- {XCODE_BETA} will be created pointing to Xcode {latest_version}.')
	else:
		current_beta = XCODE_BETA.resolve()
		print(f'- {XCODE_BETA} will stop linking to {current_beta} and start pointing to Xcode {latest_version}.')
	if not dry_run:
		latest_version_path = path_for_xcode_version(latest_version)
		make_alias(latest_version_path, XCODE_BETA)
		
	# XCODE_RELEASE is updated:
	# - 99% of the times to the newest release version (the current_beta that's about to be replaced), if that beta points to a release version
	# - If no XCODE_RELEASE version exists, to the current_beta (a prerelease version, but at least different from XCODE_BETA)
	# - If no current_beta exists, to the same version as XCODE_BETA (the only Xcode version detected).
	if XCODE_RELEASE.exists():
		current_release = XCODE_RELEASE.resolve()
		if is_release_version(current_beta):
			print(f'- {XCODE_RELEASE} will stop linking to {current_release} and start pointing to {current_beta}.')
			if not dry_run:
				make_alias(current_beta, XCODE_RELEASE)
	elif current_beta:
		print(f'- NO RELEASE VERSION DETECTED: {XCODE_RELEASE} will be created pointing to {current_beta}.')
		if not dry_run:
			make_alias(current_beta, XCODE_RELEASE)
	else:
		print(f'- NO RELEASE VERSION DETECTED: {XCODE_RELEASE} will be created pointing to {latest_version}.')
		if not dry_run:
			latest_version_path = path_for_xcode_version(latest_version)
			make_alias(latest_version_path, XCODE_RELEASE)
		
		
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
	
	try:
		all_versions = subprocess.run(['xcodes', 'list'], check=True, timeout=10, stdout=subprocess.PIPE).stdout.decode('utf-8')
	except subprocess.TimeoutExpired:
		raise AssertionError('Calling xcodes has failed. Please use "xcodes list" to ensure that it works (maybe the Apple ID is not set?)') from None # https://stackoverflow.com/a/52725410
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
	

def path_for_xcode_version(searched_version: str) -> Path:
	"""Returns the path to the provided Xcode version, if found."""
	
	installed_versions = subprocess.run(['xcodes', 'installed'], check=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
	for version in installed_versions.split("\n"):
		if searched_version in version:
			return version.split("\t")[1]
	return None
	
	
def make_alias(source: Path, destination: Path):
	"""Creates a Finder alias and a symlink to `source` on the `destination` Path."""
	
	destination.unlink(missing_ok=True) # This must be done first to avoid problems with `destination.is_dir()` returning true with this symlink
	# osascript doesn't allow to set the name of the alias on the same call, so we must only use the parent folder
	# and rename it later
	if destination.is_dir():
		destination_folder = destination
	else: # If it's a file that doesn't exists yet
		destination_folder = destination.parent
	if destination_folder == source.parent:
		raise AssertionError("Currently we don't support Finder alias on the same folder (macOS changes its name)")
	subprocess.run(['osascript', '-e', f'tell application "Finder" to make alias file to (POSIX file "{str(source)}") at (POSIX file "{str(destination_folder)}")'], check=True, stdout=subprocess.DEVNULL)
	temporal_path = destination_folder / source.name
	if source.is_dir(): # macOS delete the ".app" from app alias it creates by default...
		temporal_path = temporal_path.with_suffix('')
	if destination.is_dir():
		destination = destination / temporal_path.name # If we didn't set a name, we add the source's name
	temporal_path.rename(destination.with_suffix('.alias')) # We add this suffix to distinguish it for the symlink.
	# To be able to access Xcode from Terminal, we also need to keep a symlink.
	# TODO: If `xcodes` sets  the Command Line Tools, maybe this isn't needed
	destination.symlink_to(source)


if __name__ == '__main__':
	sys.tracebacklimit = 0 # Disables Python's Traceback, to show clearer errors.
	sys.exit(main())
