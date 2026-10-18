#!/bin/sh
set -eu
repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
bits=${1:-64}
case "$bits" in 64|32) ;; *) exit 2;; esac
out=${PROBE_OUT:-./probe-bin}
mkdir -p "$out"
export PATH=/opt/glslang/bin:$PATH
for name in egl-probe egl-probe-zink egl-probe-protected-stock; do
 gcc -m"$bits" -O2 "$repo/probes/$name.c" -o "$out/$name$bits" -lEGL -lGLESv2
done
for name in glx-probe glx-probe-zink; do
 gcc -m"$bits" -O2 "$repo/probes/$name.c" -o "$out/$name$bits" -lGL -lX11
done
gcc -m"$bits" -O2 "$repo/probes/vulkan-probe.c" -o "$out/vulkan-probe$bits" -lvulkan
glslangValidator -V "$repo/probes/compute.comp" -o "$out/compute.spv"
chmod a+r "$out/compute.spv"
