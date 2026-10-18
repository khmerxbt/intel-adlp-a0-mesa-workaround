# Integration, testing and recovery

## Start per application

Read `python3 scripts/check_device.py` output first. Only 8086:46a1 revision 00
was tested; a matching identity still does not guarantee identical hardware.
Start with `INTEL_DEBUG=noccs application`, then verify real Intel output. This
flag must be in the process environment before the driver initializes.

For the custom build, use a disposable container with the same runtime as the
intended application and mount the staged prefix read-only at `/opt/qy0z-mesa`.
Pass only the required DRM render node, preserve saves/configuration and record
kernel-log deltas. If a test wedges the GPU, stop new submissions and recover
before further tests. Do not repeatedly read `i915_gpu_info`: that debugfs access
was a separate forcewake-warning confounder in the reference investigation.

`examples/compose.iris.yaml` illustrates a 64-bit Iris/EGL/GLX application overlay.
It is not a full RomM stack and does not alter authentication, ROM mounts or
video encoders. A compatible app image must already supply its runtime loader
and driver dependencies. Test the merged Compose configuration before applying.

The probes require actual hardware output, exact expected pixels and the custom
version. Software fallback is rejected. They do not establish video-encoder health:

```sh
# Inside a compatible disposable GPU container after selecting the custom runtime:
export LD_LIBRARY_PATH=/opt/qy0z-mesa/lib/x86_64-linux-gnu
export LIBGL_DRIVERS_PATH=/opt/qy0z-mesa/lib/x86_64-linux-gnu/dri
export __EGL_VENDOR_LIBRARY_FILENAMES=/opt/qy0z-mesa/share/glvnd/egl_vendor.d/50_mesa.json
export MESA_LOADER_DRIVER_OVERRIDE=iris
unset INTEL_DEBUG
timeout --kill-after=3s 55s python3 probes/render-probe.py
timeout --kill-after=3s 55s python3 probes/render-features.py
```

Keep an independent record of fresh GPU HANG/reset/TLB errors. Absence of errors
alone is insufficient: the renderer and actual drawing results must also pass.
Use a normal render-enabled user to validate permissions before deployment.

## Headless Steam is a different display path

The reference Steam Xorg uses a dummy screen with no DRI2/DRI3 acceleration.
Direct Iris GLX failed there. Its working path preserves the existing Mesa 25
Zink frontend, legacy `LIBGL_KOPPER_DISABLE=1` / `LIBGL_KOPPER_DRI2=1`, and uses
custom ANV 26.0.8-qy0z.1 for Vulkan execution in both architectures.

`examples/compose.steam.yaml` shows that backend overlay. It does not replace
all Steam GL libraries with a newer Iris build. Do not force
`MESA_LOADER_DRIVER_OVERRIDE=zink`: on this dummy server that requested an
unsupported DRI3 swapchain path and caused cleanup errors. Do not globally point
`LD_LIBRARY_PATH` at the Iris-only runtime for this Steam layout.

The reference image needed `libegl1:i386`, `libgles2:i386` and
`libxcb-keysyms1:i386` in addition to its existing driver/runtime dependencies.
Check `ldd` and Vulkan loader diagnostics on your exact image; build a separate
image rather than installing transient packages into a running production container.
Native EGL in the reference Steam image still uses stock Iris with `noccs`.
GLX tests confirmed the custom ANV library in the Zink process; `glxinfo` alone
can still display Mesa 25 for the frontend and is not enough to identify ANV.

## Native host integration: advanced, distribution-specific

Prefer an isolated container trial before host changes. The successful reference
host build was compiled for Debian 12, not copied from Ubuntu. The deployment
copied its runtime to the OS disk under `/opt/qy0z-mesa`, added a dedicated
ldconfig entry, and retained every modified package file with package-aware
`dpkg-divert` backups. Backups also covered environment/default-loader settings.

The native host required matching DRI loader paths as well as EGL/GLX libraries:
new EGL/Gallium plus old Mesa 22 `iris_dri.so` in one Xorg process caused a
shader-cache SIGBUS. Correcting the DRI lookup fixed startup. The reference
managed native paths were:

- `/usr/lib/x86_64-linux-gnu/dri/iris_dri.so`
- `/usr/lib/x86_64-linux-gnu/dri/swrast_dri.so`
- `/usr/lib/x86_64-linux-gnu/dri/kms_swrast_dri.so`
- `/usr/lib/x86_64-linux-gnu/libvulkan_intel.so`

They pointed at the corresponding custom runtime files, with the original
package files retained under `.qy0z-distrib` diversions. `ldconfig` preferred the
custom 64-bit directory. The native Vulkan path also covered applications that
clear environment overrides. Do not indiscriminately replace an entire `/usr/lib`
tree, transplant these Debian paths to another distro, or remove upstream files
without managed recovery. No automatic root installer is provided here.

Refreshing the display session loads new host userspace libraries and interrupts
that local desktop. Already-running apps need restarting to load changed
libraries. A kernel reboot was not required for this Mesa-only deployment.
Changing the kernel driver/firmware would be a separate operation.

## Recovery record to prepare before installation

Preserve your original Compose file/image ID, environment and loader config,
package diversion state, file hashes, prefix contents and application saves.
A useful rollback should refuse to overwrite configurations changed after the
recorded deployment and must not overwrite later game progress.

For a container, restore the prior Compose/image and recreate only that service.
For a host, stop affected GPU applications, verify that each link/diversion is
still yours, restore the original package files through the package manager,
restore only your recorded configuration changes, run `ldconfig`, and refresh
the display session. Remove the custom prefix only after checking that no other
app/container depends on it. Keep recovery access separate from that desktop.

## What this does not cover

Jellyfin Quick Sync/VA-API uses Intel iHD, a separate video driver. Do not enable
video acceleration merely because these Mesa 3D tests passed. Plain virtio-vga
is not virgl or GPU passthrough. Containers do not automatically inherit host
Mesa libraries. No PCIe, BIOS, undervolt, clock, E-core or CPU-power fix is claimed.
