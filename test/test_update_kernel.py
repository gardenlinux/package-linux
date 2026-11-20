#!/usr/bin/env python3
from update_kernel import *
import update_kernel as kernel
import json

latest_versions = {
    "6.1.":  ("6.1.191",  "6.1.191-1",    "debian/6.1.190-1"),
    "6.6.":  ("6.6.161",  "6.6.161-2",    "debian/6.6.15-2"),
    "6.12.": ("6.12.115", "6.12.115-2",   "debian/${version/\\~/_}"),
    "6.18.": ("6.18.60",  "6.18.60-1",    "debian/6.18.15-1"),
    "7.2.":  ("7.2.15",   "7.2.15-1",     "debian/${version/\\~/_}"),
    "7.3.":  ("7.3.1",    "7.3.1-1~exp1", "debian/${version/\\~/_}")
}

def test_match_version():
    for version, data in latest_versions.items():
        assert match_version(version[:-1], data[1])
        assert match_version(data[0], data[1])
        assert not match_version(data[1], data[0])

    assert not match_version("6.18.1", "6.18.13-2")
    assert not match_version("6.18.1", "6.18.2-1")
    assert not match_version("6.1", "6.18.1")

def test_fetch_latest_kernel_version():
    with open("releases.json") as f:
        releases = json.load(f)["releases"]

    # LTS releases
    for version, data in latest_versions.items():
        if not version.startswith("7."):
            assert fetch_latest_kernel_version(releases, version) == data[0]

    # Non-LTS releases
    assert fetch_latest_kernel_version(releases, "7.2.", ignore_non_lts=True, allow_eol=True) == "7.2.15"

    # these must fail
    for version, params in (
        ('7.2.', {}),
        ('7.2.', {'ignore_non_lts': True}),
        ('7.2.', {'allow_eol': True})
    ):
        failed = False
        try:
            fetch_latest_kernel_version(releases, version, **params)
        except AssertionError as e:
            print(f"Expected AssertionError occurred: {e}, with {version} and {params}")
            failed = True
        if not failed:
            raise AssertionError(f"Expected an assertion error for no matching release with {version} and {params}")

def test_fetch_latest_debian_kernel_version():
    with open("ls-remote.txt") as f:
        tags = f.read()

    assert fetch_latest_debian_kernel_version(tags, "7.3.", experimental=True) == "7.3.1-1~exp1"
    assert fetch_latest_debian_kernel_version(tags, "7.2.") == "7.2.15-1"
    assert fetch_latest_debian_kernel_version(tags, "6.18.") == "6.18.15-1"
    assert fetch_latest_debian_kernel_version(tags, "6.12.") == "6.12.115-2"
    assert fetch_latest_debian_kernel_version(tags, "6.1.") == "6.1.190-1"

    failed = False
    try:
        fetch_latest_debian_kernel_version(tags, "7.3.")
    except AssertionError as e:
        print(f"Expected AssertionError occurred: {e}, with 7.3.")
        failed = True
    if not failed:
        raise AssertionError("Expected an assertion error for no matching tag with 7.3.")

def test_update_versions():
    with open("releases.json") as f:
        releases = json.load(f)["releases"]
    with open("ls-remote.txt") as f:
        tags = f.read()

    current_lts = kernel.current_lts
    try:
        # check in version upgrades
        for use_version, ignore_non_lts, experimental  in (
            ("6.1.",  False, False),
            ("6.6.",  False, False),
            ("6.12.", False, False),
            ("6.18.", False, False),
            ("7.3.",  True,  True),
        ):
            kernel.current_lts = use_version
            expected_orig, expected_version, expected_debian_ref = latest_versions[use_version]

            new_version = fetch_latest_kernel_version(
                releases, use_version, ignore_non_lts=ignore_non_lts, allow_eol=False
            )
            new_debian_version = fetch_latest_debian_kernel_version(
                tags, use_version, experimental=experimental
            )
            content = (
                f"version_orig={use_version}0\n"
                f"version={use_version}0-1\n"
                '\tdebian_ref="debian/old"\n'
            )
            py_content = f'current_lts = "{use_version}"\n'

            updated_content, updated_py_content = update_versions(
                content, py_content, new_version, new_debian_version, use_version
            )

            assert f"version_orig={expected_orig}" in updated_content
            assert f"version={expected_version}" in updated_content
            assert f'\tdebian_ref="{expected_debian_ref}"' in updated_content
            assert updated_py_content is None

        # test upgrading to a new major/minor kernel version
        for from_version, use_version, ignore_non_lts, experimental in (
            ("6.1.",  "6.6.",  False, False),
            ("6.6." , "6.12.", False, False),
            ("6.12.", "6.18.", False, False),
            ("6.18.", "7.3.",  True,  True),
        ):
            kernel.current_lts = from_version
            expected_orig, expected_version, expected_debian_ref = latest_versions[use_version]

            new_version = fetch_latest_kernel_version(
                releases, use_version, ignore_non_lts=ignore_non_lts, allow_eol=False
            )
            new_debian_version = fetch_latest_debian_kernel_version(
                tags, use_version, experimental=experimental
            )
            content = (
                f"version_orig={from_version}60\n"
                f"version={from_version}60-1\n"
                f'\tdebian_ref="something"\n'
            )
            py_content = f'current_lts = "{from_version}"\n'

            updated_content, updated_py_content = update_versions(
                content, py_content, new_version, new_debian_version, use_version
            )

            assert f"version_orig={expected_orig}" in updated_content
            assert f"version={expected_version}" in updated_content
            assert f'\tdebian_ref="{expected_debian_ref}"' in updated_content
            assert f'current_lts = "{use_version}"' in updated_py_content

        # Test that updating with a mismatched current_lts raises an AssertionError
        kernel.current_lts = "6.1."
        for update_to, content, py_content in (
            ("6.18.", "", ""),
            ("6.18.", "some invalid content", ""),
            # duplicate entries
            ("6.18.", "version_orig=6.1.60\nversion=6.1.60-1\n\tdebian_ref=\"whatever\"\nversion=6.1.60-1\n", "current_lts = \"6.1.\""),
            ("6.18.", "version_orig=6.1.60\nversion=6.1.60-1\n\tdebian_ref=whatever\n", "current_lts = \"6.1.\"\ncurrent_lts = \"6.1.\"\n"),
            #("6.18.", "version_orig=6.1.60\nversion=6.1.60-1\n\tdebian_ref=whatever\n", "current_lts = \"6.1.\""),
            # one of both is missing
            ("6.18.", "", "current_lts = \"6.1.\""),
            ("6.18.", "version_orig=6.1.60\nversion=6.1.60-1\n\tdebian_ref=whatever\n", ""),
            # invalid source number
            ("6.18.", "version_orig=6.2.60\nversion=6.1.60-1\n\tdebian_ref=whatever\n", "current_lts = \"6.1.\""),
            ("6.18.", "version_orig=6.1.60\nversion=6.2.60-1\n\tdebian_ref=whatever\n", "current_lts = \"6.1.\""),
            ("6.18.", "version_orig=6.1.60\nversion=6.1.60-1\n\tdebian_ref=whatever\n", "current_lts = \"6.2.\""),
            ("6.18.", "version_orig=6.1.60\nversion=6.18.60-1\n\tdebian_ref=whatever\n", "current_lts = \"6.1.\""),
        ):
            new_version = fetch_latest_kernel_version(releases, update_to)
            new_debian_version = fetch_latest_debian_kernel_version(tags, update_to)
            failed = False
            try:
                updated_content, updated_py_content = update_versions(
                    content, py_content, new_version, new_debian_version, update_to
                )
            except AssertionError as e:
                print(f"Expected AssertionError occurred: {e}, with content: {content} / {py_content}")
                failed = True
            if not failed:
                raise AssertionError(f"Expected failure did not occur.\nwith content:\n{content}\npy_content:\n{py_content}")

        # Test with actual files content
        kernel.current_lts = current_lts
        update_to = "6.12."
        expected_orig, expected_version, expected_debian_ref = latest_versions[update_to]
        new_version = fetch_latest_kernel_version(releases, update_to)
        new_debian_version = fetch_latest_debian_kernel_version(tags, update_to)

        with open("../prepare_source", "r") as f:
            content = f.read()
        with open("../update-kernel.py", "r") as f:
            py_content = f.read()

        updated_content, updated_py_content = update_versions(
            content, py_content, new_version, new_debian_version, update_to
        )
        assert f"version_orig={expected_orig}" in updated_content
        assert f"version={expected_version}" in updated_content
        assert f'\tdebian_ref="{expected_debian_ref}"' in updated_content


    finally:
        kernel.current_lts = current_lts


def main():
    test_match_version()
    test_fetch_latest_kernel_version()
    test_fetch_latest_debian_kernel_version()
    test_update_versions()

    print("All tests passed.")

if __name__ == "__main__":
    main()
