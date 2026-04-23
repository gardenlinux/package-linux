---
title: "Kernel Flavors"
description: Available kernel variants for different architectures and use cases
related_topics:
  - /explanation/kernel.md
  - /how-to/kernel-builds.md
  - /reference/kernel-flavors.md
migration_status: "done"
migration_issue: "https://github.com/gardenlinux/gardenlinux/issues/4629"
migration_stakeholder: "@tmangold, @yeoldegrove, @ByteOtter"
migration_approved: false
github_org: gardenlinux
github_repo: package-linux
github_source_path: docs/reference/kernel-flavors.md
github_target_path: docs/reference/kernel-flavors.md
---

# Kernel Flavors

Garden Linux provides multiple kernel variants optimized for different architectures and deployment scenarios.

## Available Flavors

| Flavour     | Architecture | Description                                                    |
| ----------- | ------------ | -------------------------------------------------------------- |
| amd64       | x86_64       | 64-bit PCs; includes Intel SGX, TDX, Mellanox SmartNIC support |
| cloud-amd64 | x86_64       | Cloud VMs (AWS, Azure, GCP) - stripped-down with cloud drivers |
| arm64       | aarch64      | 64-bit ARMv8 machines                                          |
| cloud-arm64 | aarch64      | Cloud VMs (AWS, Azure, GCP) - stripped-down with cloud drivers |

Cloud flavors disable graphics, USB, wireless, Bluetooth, and audio drivers
and enable Hyper-V, virtio, Xen, ENA (AWS), GVE (GCE), and MANA (Azure).

## Further reading

- [kernel.org LTS releases](https://www.kernel.org/category/releases.html)
- [Debian kernel patches](https://salsa.debian.org/kernel-team/linux/-/tree/master/debian/patches)

## Related Topics

<RelatedTopics />
