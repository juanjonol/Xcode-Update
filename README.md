# Xcode Updater

Simplify the update of Xcode versions.

## Why?

[`xcodes`](https://github.com/RobotsAndPencils/xcodes) makes managing Xcode's versions a lot easier, but the user must still choose which versions to install or delete.

This script is a simple wrapper around `xcodes` to automate this as much as possible. 

## Usage

Simply call `xcode-update` to download a new Xcode version and delete the old one.

By default, only the latest release and beta version is preserved, but a different number can be set with the `--release` and `--betas` parameters. For example, `xcode-update --beta 2` will preserve 1 release version and 2 beta versions.

## Support

If you have a problem, create an [issue][1]. Pull request are welcome.

[1]:	https://github.com/juanjonol/Xcode-Updater/issues
