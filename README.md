# Xcode Updater

Simplify the update of Xcode versions.

## Why?

[`xcodes`](https://github.com/RobotsAndPencils/xcodes) makes managing Xcode's versions a lot easier, but the user must still choose which versions to install or delete.

This script is a simple wrapper around `xcodes` to automate this as much as possible.

This is an heavily-opinionated script that in general does the following changes:

- The latest Xcode version is always installed, no matter if it's a Beta (Prerelease) or a Release version.
- `/Applications/Xcode-beta.app` is set as a symbolic link pointing to the latest Beta.
- `/Applications/Xcode.app` is set as a symbolic link pointing to the latest Release, but only if `/Applications/Xcode-beta.app` isn't already pointing to it (there’s no point on having two links to the same version).
   - This will usually happen with Release Candidates, which are a Prerelease versions that should end up as Release versions.   
   - We can think of this as keeping the latest Release version as a Beta until it’s properly tested. so we keep the previous Release version until it's property tested.
- After everything is updated, the oldest version is deleted.
   - The oldest Release version is only deleted when `/Applications/Xcode.app` version is updated.

## Usage

Simply call `xcode-update` to download a new Xcode version and delete the old one.

## FAQ

### How do I manage multiple Xcode versions with this script?

This script only installs the newest Xcode version and deletes the oldest one. Any other Xcode version will be let untouched.

### How do I keep this script from deleting an Xcode version?

This script uses `xcodes list` to search for Xcode versions, so anything that hides the Xcode version from `xcodes` will work. For example, the Xcode version could be placed on an "Archived" subfolder.

## Support

If you have a problem, create an [issue][1]. Pull request are welcome, but keep in mind that this script is heavily tailored to how I want ot to work, so I don't intent to change its behaviour too much (unless I'm convinced otherwise).

[1]:	https://github.com/juanjonol/Xcode-Updater/issues
