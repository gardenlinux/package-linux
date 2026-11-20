#!/usr/bin/env python3
import os
from urllib.request import urlopen
import argparse
import json
import re
import subprocess
import sys

# Script to automate the process of selecting the latest patch version of linux

# Update this when we base our kernel build on a newer lts branch
current_lts = "6.18."

def match_version(version, debian_version):
    if debian_version == version:
        return True
    elif not debian_version.startswith(version):
        return False
    remain = debian_version[len(version):]
    return not remain[0].isalnum()

def fetch_latest_kernel_version(releases, use_version, ignore_non_lts=False, allow_eol=False):
    latest_current_lts = [
        r["version"]
        for r in releases
        if r["version"].startswith(use_version)
        and (r["moniker"] == "longterm" or ignore_non_lts)
        and (r["iseol"] == False or allow_eol)
    ]
    assert len(latest_current_lts) == 1, f"Expected exactly one release matching {use_version}"
    return latest_current_lts[0]

def get_latest_kernel_version(args, use_version):
    with urlopen("https://www.kernel.org/releases.json") as response:
        releases = json.loads(response.read().decode())["releases"]
        new_version = fetch_latest_kernel_version(releases, use_version, args.ignore_non_lts, args.allow_eol)
        if args.verbose:
            print(f"Latest version matching {use_version}: {new_version}")
        return new_version

def fetch_latest_debian_kernel_version(tags, use_version, experimental=False):
    build = r"" if not experimental else r"(_exp[0-9]+)?"
    rc_build = re.compile(r"^\S+\s+refs/tags/debian/" + re.escape(use_version) + r"[0-9]+-[0-9]+" + build + r"$")
    filtered_tags = [line.split()[1] for line in tags.splitlines() if rc_build.match(line)]
    assert filtered_tags, f"No tags found matching {use_version}"
    # there will be multiple tags matching, so we don't want to check for len() == 1
    latest_tag = filtered_tags[0]
    if experimental:
        latest_tag = latest_tag.replace("_", "~")
    return latest_tag.split("/")[-1]

def get_latest_debian_kernel_version(args, use_version):
    """Get the latest Debian kernel version for the current LTS branch."""
    debian_repo = "https://salsa.debian.org/kernel-team/linux.git"
    result = subprocess.run(
        ["git", "ls-remote", "--tags", "--sort=-version:refname", debian_repo, f"debian/{use_version}*"],
        capture_output=True,
        text=True,
    )
    latest_tag = fetch_latest_debian_kernel_version(result.stdout, use_version, args.experimental)
    if args.verbose:
        print(f"Latest tag matching {use_version}: {latest_tag}")
    return latest_tag

def update_line(file_path, content, search, replace):
    old_line = [line for line in content.splitlines() if line.startswith(search)]
    assert len(old_line) == 1, f"Expected exactly one line starting with {search}"
    new_content = content.replace(old_line[0], replace)
    if content != new_content:
        print(f"Updating line in file {file_path}:\n- {old_line[0]}\n+ {replace}\n")
    return new_content

def update_versions(script_content, py_content, new_version, new_debian_version, upgrade_to, verbose=False):
    # the script itself
    updated_py_content = None
    if upgrade_to != current_lts:
        print(f"Upgrading from {current_lts} to {upgrade_to}")
        updated_py_content = update_line("update-kernel.py", py_content, f'current_lts = "{current_lts}"', f'current_lts = "{upgrade_to}"')
    else:
        print(f"Updating to {new_version} (deb: {new_debian_version}) for within {upgrade_to}")

    # prepare_source
    updated_content = update_line("prepare_source", script_content, f"version_orig={current_lts}", f"version_orig={new_version}")
    if new_debian_version.startswith(new_version):
        updated_content = update_line("prepare_source", updated_content, f"version={current_lts}", f"version={new_debian_version}")
        updated_content = update_line("prepare_source", updated_content, f"\tdebian_ref=", f'\tdebian_ref="debian/${{version/\\~/_}}"')
    else:
        last_version = new_debian_version.split("-")[-1]
        updated_content = update_line("prepare_source", updated_content, f"version={current_lts}", f"version={new_version}-{last_version}")
        updated_content = update_line("prepare_source", updated_content, f"\tdebian_ref=", f'\tdebian_ref="debian/{new_debian_version}"')

    if script_content == updated_content:
        return None, None

    return updated_content, updated_py_content

def update_version_in_script(file_path, args, new_version, new_debian_version):
    old_content = ""
    old_py_content = ""
    with open(file_path, "r") as file:
        old_content = file.read()
    with open(__file__, "r") as file:
        old_py_content = file.read()

    updated_content, py_content = update_versions(
        old_content, old_py_content,
        new_version, new_debian_version,
        args.upgrade_to, args.verbose)

    if updated_content is None and py_content is None:
        return

    assert updated_content != "", "Updated content should not be empty"

    if py_content and py_content != old_py_content:
        with open(__file__, "w") as file:
            file.write(py_content)

    if updated_content != old_content:
        with open(file_path, "w") as file:
            file.write(updated_content)

def main():
    # parse args for --experimental
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--experimental", "-e", action="store_true", help="Enable experimental kernel version")
    parser.add_argument("--match-debian-kernel", "-m", action="store_true", help="Ensure the Debian kernel version matches the upstream kernel version")
    parser.add_argument("--ignore-non-lts", "-i", action="store_true", help="Ignore non-LTS kernel versions")
    parser.add_argument("--allow-eol", "--eol", action="store_true", help="Allow EOL (End of Life) kernel versions")
    parser.add_argument("--file", default="prepare_source", help="Specify the file to update the kernel version in")
    parser.add_argument("--upgrade-to", default=current_lts, help="Specify the kernel version to upgrade to")
    args = parser.parse_args()
    if not args.upgrade_to.endswith("."):
        args.upgrade_to += "."

    new_version = get_latest_kernel_version(args, args.upgrade_to)
    new_debian_version = get_latest_debian_kernel_version(args, args.upgrade_to)
    if new_debian_version is None:
        print(f"No Debian version found for {new_version}")
        return
    elif args.match_debian_kernel and not new_debian_version.startswith(new_version):
        print(f"Debian version {new_debian_version} is older than {new_version}")
        return

    update_version_in_script(args.file, args, new_version, new_debian_version)

    if args.upgrade_to != current_lts and (
        (os.path.exists("fixes_debian") and os.listdir("fixes_debian")) or
        (os.path.exists("upstream_patches") and os.listdir("upstream_patches"))
    ):
        print(f"WARNING: Kernel upgraded to {args.upgrade_to} while there are existing fixes or patches")
        print("\tPlease review which fixes or patches may need to be updated or removed.")


if __name__ == "__main__":
    main()
