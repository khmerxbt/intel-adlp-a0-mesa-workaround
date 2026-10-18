# QY0Z engineering-sample graphics investigation — 18 October 2026

## Findings

The strongest new lead is a removed upstream hardware workaround, not a verified community binary driver. Intel's Mesa commit `f7e39c6f8545540ed573a6b1036710b55f7d6778` removed `Wa_22011186057` in August 2023 because ADL-P A0 was considered pre-production hardware. The removal shipped in Mesa 23.3. The former condition is exactly `platform == INTEL_PLATFORM_ADL && gt == 2 && revision == 0`. The NAS is PCI 8086:46a1 revision 00, reports graphics A0, and has been tested with Mesa 26.0.8, whose source no longer contains the restriction.

This makes restoring the restriction a hardware-specific candidate, **not proof of root cause**. Earlier tests changed the kernel while retaining recent Mesa. Kernel CCS0 compute-engine disablement is a different mechanism from CCS image/surface compression. Both use the acronym CCS; disabling the compute engine did not test the image-compression hypothesis.

The new Mesa patch restores the historical format restriction, rejects affected compressed-buffer modifiers in Iris, and blocks compressed modifiers in common ISL scoring, even when an override asks for one. Uncompressed buffers remain available. The scope is ADL GT2 revision 0, following the historical upstream scope, rather than all Intel GPUs. It does not change clocks, voltage, firmware, kernel engine topology, EU counts or CPU power limits. ANV shares the changed ISL policy, but a successful OpenGL test would not establish Vulkan or video-encoding health.

## Primary upstream evidence

- [Mesa 21.2 release notes](https://docs.mesa3d.org/relnotes/21.2.0.html): lists the introduction of Wa_22011186057. Official source archive was downloaded and checked against its published SHA256 `0cb3c802f4b8e7699b1602c08c29d06a4d532ab5b8f7a64676c4ca6bb8f4d426`. Its ISL source explicitly rejects CCS for ADL GT2 revision 0.
- [Mesa removal commit](https://gitlab.freedesktop.org/mesa/mesa/-/commit/f7e39c6f8545540ed573a6b1036710b55f7d6778), [merge request 24699](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/24699), [23.3 release notes](https://docs.mesa3d.org/relnotes/23.3.0.html). Direct GitLab access was unavailable; exact Intel-authored commit and diff were retrieved through a public Git mirror and preserved in ../evidence/upstream-removal.json. The diff removes the original condition from `isl_format_supports_ccs_e`.
- [Linux introduction, 1a791036](https://github.com/torvalds/linux/commit/1a7910368cba1e76b992b116fc8ba28503e6dcc1): identifies buffer compression as unusable on A stepping; blocks RC/MC compressed display modifiers.
- [Linux removal, e7dfd7c](https://github.com/torvalds/linux/commit/e7dfd7c60e402e658238d25c8da4f8645e45b982): removes pre-production A-step display restrictions in October 2024. This is the **display** restriction, not a general rendering fix. Our older MT65 kernel port retained it and still hung, while recent Mesa remained in use.
- [Mesa 26.0.8 source](https://archive.mesa3d.org/mesa-26.0.8.tar.xz), [published checksum](https://docs.mesa3d.org/relnotes/26.0.8.html): SHA256 `caf1c0061a68e88dfa74967a7e780c0e85d65b6c4e334cd69095a5dc54ad78bc`. Pinned as this experiment's base to avoid changing unrelated versions.
- [Mesa debug variables](https://docs.mesa3d.org/envvars.html) and [debugging methodology](https://docs.mesa3d.org/graphics-debugging/debugging-misrenderings-crashes.html): existing `INTEL_DEBUG=noccs` is a useful unmodified-driver control. `nofc` and `nohiz` would be additional variables and should be separate later experiments.

## Chinese community evidence and applicability

Searches included QY0Z/QXSG, 12700H ES, 906A0, 核显, Linux, i915, 驱动, 黑屏, 死机, 修复, SR-IOV, and source/commit searches. Search visibility is incomplete; absence of a result is not proof that nobody has a fix. No verified exact-QY0Z Linux 3D fix was found.

| Source | What it establishes | Limitation |
| --- | --- | --- |
| [TOPC manufacturer Bilibili guide](https://www.bilibili.com/opus/952120444871245826) | Explicitly names QY0Z/QXSG; Windows installation/driver tools and hardware troubleshooting | No pinned Linux rendering fix, no evidence for changing the reference board firmware |
| [QY0Z owner review](https://www.bilibili.com/video/BV13hAWeDEJE/) | Exact sample family; accessible description/comments discuss board/memory/BIOS | Full comment collection requires login; public API returned HTTP 412; no claim to have inspected unavailable comments or watched all video content |
| [TOPC QY0Z review](https://www.bilibili.com/video/BV1sM4m1z7f1/) | Search-indexed exact board family | No reproducible Linux driver fix established |
| [G660 12700H Bilibili review](https://www.bilibili.com/video/BV1s14y1f7yg/) | Author's description reports Linux hardware-transcode limitation | Different board; exact sample unspecified; description is not a 3D reproduction |
| [CCBP PVE/SR-IOV guide](https://www.amrzs.net/2024/11/03/pve_sriov_gpu/) | N100, kernel 6.8.4-2-pve: alternate Intel backport avoids a GuC HWCONFIG failure and enumerates VFs | Different silicon; VF enumeration is not ADL A0 rendering validation |
| [Chinese PVE guide](https://foxi.buduanwang.vip/virtualization/pve/2695.html/) | Reports 12th-gen ES Windows VF/code-43 issue | Guest Windows virtualization, not host Iris 3D |
| [fnOS DG1 adaptation](https://blog.kkk.rs/archives/36), [owner list](https://blog.kkk.rs/archives/29) | Public experience with separate DG1 cards and adapted drivers on NAS systems | Discrete DG1 support is not an integrated QY0Z repair; did not execute unknown package installers |
| [Tieba QY0Z board post](https://tieba.baidu.com/p/8877666740), [V2EX build](https://global.v2ex.com/t/1196379) | Board/sample identification and user builds | No tested host iGPU source fix |

[This owner report](https://winraid.level1techs.com/t/request-upgrades-microcode-for-10729-china-diy-1280p/105982/7) points to the Chinese SR-IOV guide and describes kernel-version differences on TOPC 12700H ES. Exact CPUID and 3D validation are missing. That lead motivated the earlier MT65 port, which we actually built and tested unsuccessfully.

[The exact-QY0Z/QXSG Reddit reports](https://www.reddit.com/r/EryingMotherboard/comments/1q8y6ry/qy0z_intel_uhd_iris_xe_graphics_linux_driver_issue/) independently describe failures across several distros, including Mesa 25.0.7/kernel 6.14. They are primary owner anecdotes, not a demonstrated fix.

The previously supplied [Arch thread](https://bbs.archlinux.org/viewtopic.php?id=275302&p=2) ends with a CPU energy-preference change on different hardware (Tiger Lake); it is not evidence of an ES hang repair. Generic CSDN articles without exact hardware/logs and the Bazzite SR-IOV repackaging repo were excluded as proof of an ES fix.

## Existing machine evidence

The MT65 rev2 trial initialized a real Intel renderer but failed the first RGB clear/readback, then RCS0 preemption timeout and chip reset. It was rolled back. Its cached compressed batch was decoded offline (no live debugfs capture): active instruction address falls at batch offset 0x648, a PIPE_CONTROL with flags 0x10007021 after a 3D draw. This identifies a synchronization/flush point at the stall, not necessarily the faulty command. It is compatible with earlier rendering failing; it does not prove a compression bug.

An fnOS media-service `i915_gpu_info` access produced a forcewake warning before the rendering test. This remains a separate confounder. Do not repeatedly read that debugfs file during new tests. The recovered boot uses the original 2026.05.06-sriov image; normal on-disk module selection differs from the loaded initramfs module. Keep that baseline explicit.

## Actual recovered baseline before this trial

Read-only inspection on this same recovered boot found `enable_guc=-1` (automatic), `max_vfs=7`, zero enabled VFs, GuC submission/SLPC/RC active, and a 100–1100 MHz permitted graphics range. The previous 600 MHz limit and GuC-off test settings are **not active in the recovered original initramfs**. Startup still reports GuC request 0x4100 failure 201/0, missing HWCONFIG, a DMC storage-start warning and the known forcewake warning. There was no RCS GPU HANG or failed chip reset before our probe. A failed Mesa-only trial on this baseline does not isolate the workaround from these remaining kernel/firmware defects. No scheduler or frequency change was made during the trial.

## Validation gate

Build and non-GPU tests first. Then one bounded hardware clear/readback and shader test with the custom Mesa, verifying real Intel renderer, correct pixels and no fresh kernel hang/reset/TLB errors. Inspect loaded libraries to prove the custom driver was used. A failure that wedges the GPU requires recovery before another trial. Do not call a successful build, software fallback, video playback, or a zero wedge flag a rendering fix. Only after basic rendering passes should PCSX2, Vulkan and VA-API be tested separately.

## Current validation status

The first rendering probes passed, followed by game/streaming trials and native
OpenGL/Vulkan host and Steam tests. See [validation.md](validation.md) for the
final matrix and limits. The validation gate above records the original test
method; statements about untested APIs in the initial investigation are not
intended to supersede the later results.
