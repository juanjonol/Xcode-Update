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


# Directory to contain symlinks to the latest Xcode versions.
XCODE_SYMLINK_DIRECTORY = Path('/Applications')
# Name for the latest Xcode release version.
XCODE_RELEASE = 'Xcode.app'
# Name for the latest Xcode prerelease version.
XCODE_BETA = 'Xcode-beta.app'
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
	
	xcode_directory = os.environ.get('XCODES_DIRECTORY')
	if not xcode_directory:
		xcode_directory = '/Applications'
	if not os.access(xcode_directory, os.R_OK | os.W_OK):
		raise PermissionError(f"The current user doesn't have permissions to install Xcode on {xcode_directory}")
	
	
def install_latest_xcode(dry_run: bool):
	"""Install the latest Xcode version, if it isn't already installed."""
	
	latest_version, is_installed = latest_xcode_version()
	if is_installed:
		print(f'{latest_version} is already installed. Nothing to do.')
		exit()
	print(f'- Xcode version {latest_version} will be installed.')
	
	if not dry_run:
		subprocess.run(['xcodes', 'install', f'{latest_version}'], check=True)


def delete_xcode(dry_run: bool):
	"""Deletes the oldest Xcode version."""

	# Xcode release versions are only updated when the current beta (that's about to be replaced) points to a release version
	xcode_beta_path = XCODE_SYMLINK_DIRECTORY / XCODE_BETA
	current_beta = xcode_beta_path.resolve()
	should_delete_release_version = is_release_version(current_beta)
	xcode_version_to_delete = oldest_xcode_version(include_releases=should_delete_release_version)
	if xcode_version_to_delete:
		print(f'- {xcode_version_to_delete} will be deleted.')
	
	if not dry_run:
		shutil.rmtree(str(xcode_version_to_delete))
		
		
def update_links(dry_run: bool):
	"""Updates the links to the latest Xcode version."""

	latest_version, latest_version_is_installed = latest_xcode_version()
	current_beta = None
	xcode_beta_path = XCODE_SYMLINK_DIRECTORY / XCODE_BETA
	xcode_release_path = XCODE_SYMLINK_DIRECTORY / XCODE_RELEASE
	if not xcode_beta_path.exists():
		print(f'- {xcode_beta_path} will be created pointing to Xcode {latest_version}.')
	else:
		current_beta = xcode_beta_path.resolve()
		print(f'- {xcode_beta_path} will stop linking to {current_beta} and start pointing to Xcode {latest_version}.')
	if not dry_run:
		if not latest_version_is_installed:
			raise AssertionError(f"Xcode {latest_version} isn't installed yet.")
		latest_version_path = path_for_xcode_version(latest_version)
		make_alias(latest_version_path, xcode_beta_path)
		
	# XCODE_RELEASE is updated:
	# - 99% of the times to the newest release version (the current_beta that's about to be replaced), if that beta points to a release version
	# - If no XCODE_RELEASE version exists, to the current_beta (a prerelease version, but at least different from XCODE_BETA)
	# - If no current_beta exists, to the same version as XCODE_BETA (the only Xcode version detected).
	if xcode_release_path.exists():
		current_release = xcode_release_path.resolve()
		if is_release_version(current_beta):
			print(f'- {xcode_release_path} will stop linking to {current_release} and start pointing to {current_beta}.')
			if not dry_run:
				make_alias(current_beta, xcode_release_path)
	elif current_beta:
		print(f'- NO RELEASE VERSION DETECTED: {xcode_release_path} will be created pointing to {current_beta}.')
		if not dry_run:
			make_alias(current_beta, xcode_release_path)
	else:
		print(f'- NO RELEASE VERSION DETECTED: {xcode_release_path} will be created pointing to {latest_version}.')
		if not dry_run:
			latest_version_path = path_for_xcode_version(latest_version)
			make_alias(latest_version_path, xcode_release_path)
		
		
def ask_for_confirmation(prompt: str):
	"""Shows the prompt and waits for the user to answer. If the user answer "No", the program is halted."""
	
	answer = None
	while answer not in ('y', 'n', ''): # '' = "Enter" key, by default we let the script continue
		answer = input(prompt)
		if answer: # If the answer is the enter key, the string is empty
			answer = answer[0].lower()
	if answer == 'n':
		exit()
	
	
def latest_xcode_version() -> (str, bool):
	"""Returns the latest Xcode version available, and if it's already installed"""
	
	try:
		all_versions = subprocess.run(['xcodes', 'list'], check=True, timeout=10, stdout=subprocess.PIPE).stdout.decode('utf-8')
	except subprocess.TimeoutExpired:
		raise AssertionError('Calling xcodes has failed. Please use "xcodes list" to ensure that it works (maybe the Apple ID is not set?)') from None # https://stackoverflow.com/a/52725410
	latest_version = all_versions.split("\n")[-2] # The last string (-1 on the array) is always empty
	is_installed = False
	if XCODES_INSTALLED_MAGIC_STRING in latest_version:
		latest_version = latest_version.replace(XCODES_INSTALLED_MAGIC_STRING, '')
		is_installed = True
	return latest_version, is_installed
	
	
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
			return Path(version.split("\t")[1])
	return None # There could be no previous Xcode versions
	

def path_for_xcode_version(searched_version: str) -> Path:
	"""Returns the path to the provided Xcode version, if found."""
	
	installed_versions = subprocess.run(['xcodes', 'installed'], check=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
	for version in installed_versions.split("\n"):
		if searched_version in version:
			return Path(version.split("\t")[1])
	return None
	
	
def make_alias(source: Path, name: str):
	"""
	Creates a Finder alias and a symlink to `source` with the given `name` to the following destination:
	- The symlink is added to `XCODE_SYMLINK_DIRECTORY`.
	- The Finder alias is added to the same folder as `source`.
	 """
	
	alias_destination = source.parent / name
	if source == alias_destination:
		raise AssertionError(f"The destination path for the alias ({alias_destination}) is the same as its source (it would override it)")
	alias_destination.unlink(missing_ok=True) # I don't think this is needed anymore: I think Applescript always overrides the original alias if present
	applescript = """
	use framework "Foundation"
	set nil to missing value
	set source to "%s"
	set destination to "%s"
	
	# Get source's URL
	set sourceURL to current application's NSURL's fileURLWithPath:source
	set {success, resolveError} to sourceURL's checkResourceIsReachableAndReturnError:(reference)
	if not success or resolveError is not missing value then
		error resolveError's localizedDescription as text
	end if
	
	# Get source's bookmark (alias)
	set options to current application's NSURLBookmarkCreationSuitableForBookmarkFile
	set {sourceBookmark, resolveError} to sourceURL's bookmarkDataWithOptions:options includingResourceValuesForKeys:nil relativeToURL:nil |error|:(reference)
	if resolveError is not missing value then
		error resolveError's localizedDescription as text
	end if

	# Make bookmark (alias)
	set destinationURL to current application's NSURL's fileURLWithPath:destination
	set {success, resolveError} to current application's NSURL's writeBookmarkData:sourceBookmark toURL:destinationURL options:options |error|:(reference)
	if not success or resolveError is not missing value then
		error resolveError's localizedDescription as text
	end if
	
	log "Successfully created alias for " & source & " at " & destination
	"""%(str(source), str(alias_destination))
	subprocess.run(['osascript', '-e', applescript], check=True)
	
	# To be able to access Xcode from Terminal, we also need to keep a symlink.
	# TODO: If `xcodes` sets  the Command Line Tools, maybe this isn't needed
	symlink_destination = XCODE_SYMLINK_DIRECTORY / name
	if source == symlink_destination:
		raise AssertionError(f"The destination path for the symlink ({symlink_destination}) is the same as its source (it would override it)")
	symlink_destination.unlink(missing_ok=True) # I'm not sure if this is needed anymore
	symlink_destination.symlink_to(source)


if __name__ == '__main__':
	sys.tracebacklimit = 0 # Disables Python's Traceback, to show clearer errors.
	sys.exit(main())
