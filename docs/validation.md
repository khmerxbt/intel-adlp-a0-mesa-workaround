# Validation record

Reference: QY0Z i7-12700H ES, Intel ADL GT2, PCI 8086:46a1 revision 00,
fnOS/Debian 12 host, kernel 6.18.18.c1126-trim and loaded i915
2026.05.06-sriov. No kernel, firmware, BIOS, clock or CPU power change was made
for the Mesa trials. GuC automatic scheduling remained active, with no enabled VFs.

## Evidence hierarchy

1. The upstream source history identifies a matching removed A0 workaround.
2. Six relevant ISL suites passed, including unaffected stepping/device controls,
   actual surface allocation and modifier-override checks.
3. Real Intel output was checked with RGB pixels, sustained shaders, depth,
   stencil, texture copies/sampling and 4× MSAA resolve. Custom libraries were
   confirmed in process mappings. Stock Mesa with `INTEL_DEBUG=noccs` also passed.
4. God of War II opening combat was sampled in PCSX2 2.6.3: 1× 512×448 about
   60 FPS, 2× 1024×896 about 60 FPS, 3× 1536×1344 about 50 FPS. These are sampled
   emulator counters, not standardized averages. 2× was selected. A 1080p stream
   is not the same as 1080p internal rendering.
5. Live streaming delivered 653 H.264 frames over 22.03 seconds (about 29.82 FPS)
   at 1920×1080, independently decoded. There were 1,100 audio packets and
   WebSocket keyboard menu/resume actions. This was not a subjective listening,
   A/V latency or every-browser test.
6. Native host OpenGL and Vulkan passed actual drawing/computation. Native
   default Vulkan discovery also passed with graphics overrides explicitly unset.
   The desktop loaded the matching custom Iris/EGL/Gallium components.
7. Both Steam architectures passed final live normal-user tests: 300 EGL shader
   draws, 300 GLX shader draws and 300 Vulkan dispatches (307,200 checked values)
   per architecture. GLX tests confirmed the patched ANV library inside Zink and
   exited cleanly. Native EGL uses stock Iris with compression disabled.

[Regression summaries](../evidence/regression-summary.json),
[Steam live results](../evidence/steam-live-tests.json),
[host GLX information](../evidence/host-glxinfo.txt) and
[default Vulkan test](../evidence/host-default-vulkan-test.txt) are sanitized
reference evidence. They are records, not CI results from arbitrary hardware.

No new GPU hang/reset messages were found in the bounded final kernel-log deltas.
No NAS reboot was required for this userspace deployment. Host display and Steam
sessions were refreshed; unrelated services and the existing VM stayed running.

## Important negative and incomplete results

Earlier alternate-kernel, GuC, frequency and power experiments did not establish
a durable rendering fix. Disabling E-cores was not isolated as a solution. The
CCS compute-engine experiment did not test image compression. A historical
PIPE_CONTROL stall location is a synchronization observation, not proof that
that command or compression caused every hang.

A same-boot stock-default compression-enabled A/B trial was not performed.
Existing GuC HWCONFIG, DMC and forcewake warnings remain. Video decode/encode,
Jellyfin/iHD, OpenCL, accelerated VM guests and hours of gaming remain unvalidated.
The current plain virtio-vga/VNC guest is not a GPU passthrough/virgl test.

## Integration failures that were corrected

The host first loaded new EGL/Gallium and old Mesa 22 Iris DRI in one Xorg process.
It hit a CPU-side shader-cache SIGBUS. Matching the DRI loader paths corrected
startup. This was not a new GPU HANG; do not dismiss a mixed installation as
hardware failure or fix it by blindly deleting all caches.

Steam’s dummy X server could not create direct Iris GLX contexts. Forcing the
Zink loader requested a DRI3 presentation path that this server lacked, producing
shutdown errors. Preserving the existing legacy Zink route with the patched
Vulkan backend passed final GLX drawing and clean teardown. The Steam frontend
is still Mesa 25.0.7; ANV is 26.0.8-qy0z.1. This is intentional and recorded,
not a claim that every Steam graphics library was replaced.

The 32-bit regression initially caught strtoul truncating a 64-bit modifier.
Changing it to strtoull fixed the real portability defect without relaxing the
assertions. Early live-probe shader-file permissions were also corrected before
the final normal-user tests. Failed attempts are not counted as final successes.
