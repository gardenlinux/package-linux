# Kernel builds for Garden Linux

This repository contains the code for building the [kernel](https://www.kernel.org) in Garden Linux.
The build is based on [the debian kernel build](https://salsa.debian.org/kernel-team/linux).

Garden Linux includes the latest LTS version of the kernel.

## Components of this repository

`./config` contains Garden Linux specific build configuration for the kernel.

`./fixes-debian` contains patches for the debian build if needed.
We apply all patches from debian by default.
In some cases, we need to make changes to those to get a working build.

`./upstream-patches` contains kernel patches that are not included in debian's kernel, but are part of the Garden Linux kernel.

`./prepare_source` contains a shell script that merges debian's kernel build repository with the upstream kernel sources.

`./update-kernel.py` contains a script which helps keeping up with patch releases of the LTS kernel version.

`.github/workflows/pr-if-new-kernel.yml` contains the workflow to create new PRs based on `./update-kernel.py` if new patch versions of the LTS kernel are available.

`.github/workflows/build.yml` contains the workflow to build and release the kernel binaries.

## Backports 

| branch | description |
| ------------- | -------------- |
| `main` | latest lts kernel we maintain (6.18) |
| `maint-6.12` | maintenance of source code for kernel 6.12 |
| `maint-6.6` | maintenance of source code for kernel 6.6 | 
| `rel-1877` | backport for 1877, merge code from `maint-6.12` | 
| `rel-1592` | backport for 1592, merge code from `maint-6.6` |


The main branch of this repository always contains the latest kernel available in Garden Linux, and in the nightly builds.
Typically, this will be the most recent long term support (LTS) line from kernel.org, but from time to time it might also be a 'stable' kernel that will become the next LTS.

We maintain also older supported kernel versions, if they are required by supported Garden Linux versions.

Any kernel version that we need to maintain other than the latest LTS in main, are maintained in `maint-<MAJOR.MINOR>` branches (e.g. `maint-6.6`).
Backport releases need to branch off from the respective `maint-<MAJOR.MINOR>` branch and include the corresponding `.container` file for target backport.

Branches containing the `.container` file must be named according to the `rel-MAJOR` naming scheme (e.g. `rel-1443`).

## How to do a backport from maint-X.Y branch

```
git checkout rel-MAJOR
git merge --squash origin/maint-x.y 
# resolve merge conflicts
git commit
git push
# Pipeline builds new rel-MAJOR version
```

> [!Tip]
> You can find out the correct `.container` file by copying it from the corresponding tag of the https://github.com/gardenlinux/repo branch, for example [1877.0](https://github.com/gardenlinux/repo/blob/1877.0/.container)

> [!Note]
> We must create `rel-*` branches to include the respective `.container` file, and not use `maint-*` for backports. This is required because multiple releases can use the same kernel version (e.g. `rel-1443` and `rel-1592` both use `maint-6.6`) 

## Automated kernel patch level upgrades 

A scheduled workflow scans a list of configured branches [see](https://github.com/gardenlinux/package-linux/blob/main/.github/workflows/pr-if-new-kernel.yml#L12), and bumps the patch level of the version defined in the prepare_source file.
The automation creates a PR if a new patch level is available.

> [!Important]  
> Note that build failures in this PR will not be visible in the way you are used to it.
> This is due to limitations on GitHub.
> Always check the PR-related workflow manually before merge as it might well be that an upgrade of the kernel breaks the build.
> [See this issue for more information if you are interested](https://github.com/gardenlinux/package-linux/issues/47).

> [!Note]
> This is done via the [update-kernel.py](https://github.com/gardenlinux/package-linux/blob/main/update-kernel.py) tool

## Config generation from debian and garden linux

Script(get_config.sh) takes prepare_source as input for kernel version and generates

1. Final debian kernel configuration file
2. Garden Linux kernel configuration file

### Container Image
Script should be executed inside repo-debian-snapshot container
```
Image: ghcr.io/gardenlinux/repo-debian-snapshot
```

### Volume Mount
```
-v package-linux:/workspace: Mounts the local package-linux directory to /workspace in the container
```

### Usage Examples

#### For AMD64 Architecture
```
podman run -v package-linux:/workspace ghcr.io/gardenlinux/repo-debian-snapshot:1764836249-amd64 /workspace/get_config.sh
```
#### For ARM64 Architecture
```
podman run -v package-linux:/workspace ghcr.io/gardenlinux/repo-debian-snapshot:1764836249-arm64 /workspace/get_config.sh
```
### Important Notes
> Final config files are copied in package-linux folder
 
> If debian_version and kernel_version is not specified , then default version from prepare_source is used.

## Comparision of kernel configs

Script (compare-config.py) compares 2 input config files and generates the differences in 3 sections (Added, Removed, Modified)

Output needs to be manually verified

### Example output

```
REMOVED:
CONFIG_ACPI_EC_DEBUGFS=y
CONFIG_ACPI_VIOT=y
CONFIG_BCACHEFS_FS=m
CONFIG_BCACHEFS_POSIX_ACL=y
CONFIG_BCACHEFS_QUOTA=y
CONFIG_BCACHEFS_SIX_OPTIMISTIC_SPIN=y

ADDED:
CONFIG_CC_HAS_COUNTED_BY=y
CONFIG_CPU_FREQ_DEFAULT_GOV_PERFORMANCE=y
CONFIG_DEBUG_INFO_BTF=y

CHANGED:
CONFIG_CC_VERSION_TEXT: x86_64-linux-gnu-gcc-14 (Debian 14.3.0-10) 14.3.0 -> x86_64-linux-gnu-gcc (Debian 15.2.0-9) 15.2.0
CONFIG_GCC_VERSION: 140300 -> 150200
```