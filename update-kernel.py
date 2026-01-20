from urllib.request import urlopen
import json
import sys

# Script to automate the process of selecting the latest patch version of linux

# Update this when we base our kernel build on a newer lts branch
current_lts = "6.18"


def get_latest_kernel_version():
    with urlopen("https://www.kernel.org/releases.json") as response:
        releases = json.loads(response.read().decode())["releases"]
        latest_current_lts = [
            r["version"]
            for r in releases
            if r["version"].startswith(current_lts)
            # (not officially lts yet ) and r["moniker"] == "longterm"
            and r["iseol"] == False
        ]
        assert len(latest_current_lts) == 1
        new_version = latest_current_lts[0]
        return new_version

def update_version_in_script(file_path, new_version):
    script_content = ""
    updated_content = ""
    with open(file_path, "r") as file:
        script_content = file.read()
        version_orig_line = [
            y for y in script_content.splitlines() if y.startswith("version_orig")
        ]
        assert len(version_orig_line) == 1
        old_version = version_orig_line[0].split("=")[1]
        assert old_version.startswith(current_lts)

        if old_version == new_version:
            sys.exit(0)

        print(f"{old_version} -> {new_version}")
        updated_content = script_content.replace(old_version, new_version, 1)

    with open(file_path, "w") as file:
        file.write(updated_content)


def main():
    new_version = get_latest_kernel_version()
    update_version_in_script("prepare_source", new_version)


if __name__ == "__main__":
    main()
