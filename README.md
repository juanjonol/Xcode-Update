# Xcode Update

Simplify the update of Xcode versions.

## Why?

[`xcodes`](https://github.com/RobotsAndPencils/xcodes) makes managing Xcode's versions a lot easier, but the user must still choose which versions to install or delete. This script is a simple wrapper around `xcodes` to automate this as much as possible.

This is an heavily-opinionated script that in general does the following:

- The latest Xcode version is always installed, no matter if it's a Beta (Prerelease) or a Release version.
- `/Applications/Xcode-beta.app` is set as a symbolic link pointing to the latest Beta.
- `/Applications/Xcode.app` is set as a symbolic link pointing to the latest Release, but only if `/Applications/Xcode-beta.app` isn't already pointing to it (there’s no point on having two links to the same version).
   - This will usually happen with Release Candidates, which are a Prerelease versions that should end up as Release versions.
   - This basically sets the latest Release version as a Beta until it’s properly tested, so we keep the previous Release version in case it's needed.
- After everything is updated, the oldest version is deleted.
   - The oldest Release version is only deleted when `/Applications/Xcode.app` version is updated.
- Two Finder alias, `Xcode-beta.alias` and `Xcode.alias`, are created on the same folder where Xcode is installed. This alias point to the same versions as the symlinks, but they can be added to macOS Dock.

## Usage

Simply call `xcode-update` to download a new Xcode version and delete the oldest one (if there's any). See `xcode-update --help` for advanced options.

## FAQ

### How do I manage multiple Xcode versions with this script?

This script only installs the newest Xcode version and deletes the oldest one, any other Xcode version will be let untouched. For example, if you want to always keep the two latest Xcode versions, you can install the second one without deleting the previous version, and after that the script will only delete the oldest of the two versions automatically.

### How do I keep this script from deleting an Xcode version?

The `--skip-delete` parameter can be used to avoid deleting the oldest Xcode version.

To permanently protect an Xcode version for deletion, anything that hides that version from `xcodes list` will work. For example, the Xcode version could be placed on an "Archived" subfolder.

### How do I change the directory where Xcode versions are installed?

With the environment variable [`XCODES_DIRECTORY`](https://github.com/RobotsAndPencils/xcodes/pull/126).

## Support

If you have a problem, create an [issue][1]. Pull request are welcome, but keep in mind that this script is heavily tailored to how I want it to work, so I don't intent to change its behaviour too much (unless I'm convinced otherwise).

[1]:	https://github.com/juanjonol/Xcode-Update/issues
