#!/bin/bash
set -e

build_amd64_output="$(python3 /work/debian-linux/debian/bin/buildcheck.py debian/build/build_amd64_none_amd64 amd64 none amd64 build)"
build_arm64_output="$(python3 /work/debian-linux/debian/bin/buildcheck.py debian/build/build_arm64_none_arm64 arm64 none arm64 build)"

echo $build_amd64_output

pushd /work/debian-linux/debian/config

/work/debian-linux/debian/bin/kconfig.py xx $build_amd64_output

# /work/debian-linux/debian/bin/kconfig.py xx /work/config/config.gardenlinux

cat xx
