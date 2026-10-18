# Intel ADL-P A0 Mesa workaround

Experimental Linux graphics workaround for **Alder Lake GT2 revision 0 engineering samples**,
validated on one **QY0Z / i7-12700H ES**, PCI **8086:46a1 revision 00**.

It restores the retired **Wa_22011186057** surface-compression restriction in
Mesa 26.0.8 and adds compressed-modifier guards. This is a Mesa userspace patch,
**not a replacement i915 kernel driver or a BIOS repair**.

[中文说明](docs/README.zh-CN.md) · [Research and Chinese community findings](docs/research.md) ·
[Validation and limits](docs/validation.md) · [Build](docs/build.md) · [Integration and rollback](docs/integration.md)

## What worked on the reference machine

| Workload | Observed result |
| --- | --- |
| OpenGL pixels/shaders, depth/stencil, texture sampling, 4× MSAA | Passed bounded real-Intel tests |
| God of War II in PCSX2, hardware OpenGL | About 60 FPS in the sampled opening-combat scene at 1× and 2×; about 50 FPS at 3× |
| Streaming | 1920×1080 at about 30 delivered FPS; keyboard and audio packet delivery verified |
| Native Debian 12 host | Custom Iris/OpenGL and ANV/Vulkan active; actual desktop verified |
| Steam Headless | 64/32-bit GLX via existing Zink frontend and patched ANV backend; shader readbacks and compute checks passed |
| Regression suites | Six relevant ISL suites passed on each architecture |

These are **single-machine, bounded tests**, not all-game averages or a guarantee of
long-term stability. No same-boot, compression-enabled stock-default A/B control was
run. Kernel/firmware warnings remain; video acceleration and other ES chips are
not validated by this project. No BIOS, firmware, ROMs, saves or game images are included.

## Start with the smallest change

Mesa already exposes a per-process compression-disable diagnostic:

```sh
INTEL_DEBUG=noccs your-application
```

It independently passed a stock-Mesa OpenGL control on the reference machine.
It affects that process and children, not other applications or containers.
Confirm a real Intel renderer, correct output and kernel-log deltas; context
creation or a successful build alone is not evidence of a fix. See Mesa’s
[documented Intel debug options](https://docs.mesa3d.org/envvars.html).

For the source patch, use the [build guide](docs/build.md). Build in a matching
container and test there before reviewing host integration. The scripts build
into a staging directory and do not install system-wide or reboot the machine.

## Why this approach

Upstream [removed the pre-production workaround](https://gitlab.freedesktop.org/mesa/mesa/-/commit/f7e39c6f8545540ed573a6b1036710b55f7d6778)
in 2023. The historical hardware condition matches the reference sample.
The patch restores that narrow condition and blocks compressed modifiers in Iris
and shared ISL scoring, including modifier overrides. It does not disable the
kernel's CCS compute engine: **CCS image compression and the CCS compute engine
are different mechanisms**.

The second patch fixes full-width DRM modifier parsing on 32-bit builds; it was
found by an unchanged regression assertion. It is not presented as a second
root cause of the original GPU hangs.

## Scope

QXSG appears in owner reports but was **not tested here**. Retail steppings,
other ES models and other boards must not be assumed equivalent. The patch's
historical ADL GT2/revision-0 scope is wider than the one tested PCI ID.

The repository contains source patches, build recipes, probes and sanitized
findings. Reusable recipes are publication adaptations of the recorded builds;
they have not yet been fully rebuilt as clean images by CI. No prebuilt binary
release is provided. Dependencies from distribution repositories can change;
source archive URLs and checksums are pinned in `sources.lock.json`.

MIT for the new project material; upstream Mesa retains its own notices.
See [NOTICE](NOTICE). Independent community work, not an Intel/Mesa/vendor-endorsed driver.
