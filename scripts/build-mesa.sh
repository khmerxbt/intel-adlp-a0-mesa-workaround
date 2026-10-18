#!/bin/sh
# Build/stage only. No host package, boot or production-app edits.
set -eu
repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
work=${QY0Z_WORK:-/work}
out=${QY0Z_OUT:-/out}
jobs=${JOBS:-4}
arch=${1:-64}
case "$arch" in 64|32) ;; *) echo 'Expected 64 or 32' >&2; exit 2;; esac
mkdir -p "$work" "$out"
source_dir="$work/mesa-26.0.8-qy0z.1"
if [ ! -d "$source_dir" ]; then
 python3 "$repo/scripts/fetch_sources.py" mesa "$source_dir"
 patch -d "$source_dir" -p1 < "$repo/patches/0001-adlp-a0-disable-ccs.patch"
 patch -d "$source_dir" -p1 < "$repo/patches/0002-isl-modifier-64bit-parser.patch"
 touch "$source_dir/.qy0z-public-patches-applied"
fi
test -f "$source_dir/.qy0z-public-patches-applied"
export PATH=/opt/glslang/bin:/opt/build-tools/bin:/usr/lib/llvm-21/bin:/usr/lib/llvm-15/bin:$PATH
export PKG_CONFIG_PATH=/opt/wayland-protocols/share/pkgconfig:/opt/spirv-tools/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}
build="$work/build$arch"
# Identical feature choices to the native reference build; scalar software fallback included.
set -- --prefix=/opt/qy0z-mesa --buildtype=release -Dgallium-drivers=iris,softpipe \
 -Dvulkan-drivers=intel -Dplatforms=x11,wayland -Dglx=dri -Degl=enabled -Dgbm=enabled \
 -Dgles1=disabled -Dgles2=enabled -Dbuild-tests=true -Dintel-rt=disabled \
 -Dgallium-va=disabled -Dvideo-codecs= -Dgallium-rusticl=false -Ddraw-use-llvm=false --wrap-mode=nofallback
if [ "$arch" = 32 ]; then
 test -x "$work/build64/src/compiler/clc/mesa_clc"
 export PATH="$work/build64/src/compiler/clc:$work/build64/src/compiler/spirv:$PATH"
 export PKG_CONFIG_LIBDIR=/usr/lib/i386-linux-gnu/pkgconfig:/usr/share/pkgconfig
 set -- "$@" --cross-file="$repo/containers/cross-i386.ini" --libdir=lib/i386-linux-gnu \
  -Dllvm=disabled -Dmesa-clc=system -Dprecomp-compiler=system -Dspirv-tools=disabled
else
 set -- "$@" --libdir=lib/x86_64-linux-gnu -Dllvm=enabled -Dshared-llvm=enabled
fi
if [ -d "$build/meson-private" ]; then
 meson setup --reconfigure "$build" "$source_dir" "$@"
else
 meson setup "$build" "$source_dir" "$@"
fi
python3 "$repo/scripts/build_selected.py" "$build" --jobs "$jobs"
meson test -C "$build" --no-rebuild --print-errorlogs isl_adlp_a0_ccs isl_surf_get_image_offset \
 isl_aux_info isl_tile_std_y isl_tilememcpy isl_surf_get_image_range_B_tile
DESTDIR="$out" meson install -C "$build" --no-rebuild
# EGL vendor selection must resolve a library for the caller's architecture.
python3 - "$out/opt/qy0z-mesa" <<'ENDPY'
import json,sys
from pathlib import Path
root=Path(sys.argv[1]);p=root/'share/glvnd/egl_vendor.d/50_mesa.json'
x=json.loads(p.read_text());x['ICD']['library_path']='libEGL_mesa.so.0';p.write_text(json.dumps(x,indent=2)+'\n')
ENDPY
printf '%s\n' "Built and staged $arch-bit runtime under $out; no host install performed."
