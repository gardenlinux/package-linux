#!/usr/bin/env python3

import sys

def extract_config_values(config_path):
    config_values = {}
    with open(config_path, 'r') as file:
        for line in file:
            if not line.strip():
                continue
            if line.startswith('#') and line.endswith(' is not set'):
                key = line.split()[1]
                config_values[key] = 'n'
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                config_values[key.strip()] = value.strip().strip('"')
    return config_values

def compare_configs(config1, config2):
    print("Comparing configuration values...")

    all_keys = set(config1.keys()) | set(config2.keys())
    added = []
    removed = []
    changed = []

    for key in sorted(all_keys):
        val1 = config1.get(key, 'not set')
        val2 = config2.get(key, 'not set')
        if val1 == 'not set' and val2 != 'not set':
            added.append(f"{key}={val2}")
        elif val1 != 'not set' and val2 == 'not set':
            removed.append(f"{key}={val1}")
        elif val1 != val2:
            changed.append(f"{key}: {val1} -> {val2}")
    if removed:
        print("REMOVED:")
        for item in removed:
            print(f"{item}")
        print()
    if added:
        print("ADDED:")
        for item in added:
            print(f"{item}")
        print()
    if changed:
        print("CHANGED:")
        for item in changed:
            print(f"{item}")

def main():
    if len(sys.argv) != 3:
        print (sys.argv)
        print("Usage: python compare.py <config1> <config2>")
        sys.exit(1)
    else:
        config1 = sys.argv[1]
        config2 = sys.argv[2]
        config1_val = extract_config_values(config1)
        config2_val = extract_config_values(config2)
        compare_configs(config1_val, config2_val)

    
if __name__ == "__main__":
    main()
