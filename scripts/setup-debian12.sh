#!/bin/sh
# This recipe is for the isolated builder image, not a NAS host.
set -eu
export DEBIAN_FRONTEND=noninteractive
dpkg --add-architecture i386
apt-get update
apt-get install -y --no-install-recommends build-essential gcc-multilib g++-multilib \
 ninja-build pkg-config python3-venv python3-mako python3-ply python3-yaml python3-packaging \
 libdrm-dev libexpat1-dev libzstd-dev zlib1g-dev libx11-dev libxext-dev libxfixes-dev libxrandr-dev \
 libxshmfence-dev libxcb-shm0-dev libxcb-xfixes0-dev libxcb-xinput-dev libxxf86vm-dev \
 libxcb-glx0-dev libxcb-dri2-0-dev libxcb-dri3-dev libxcb-present-dev libxcb-sync-dev libxcb-randr0-dev \
 libwayland-dev libwayland-egl-backend-dev wayland-protocols libglvnd-dev bison flex libelf-dev \
 libudev-dev libgtest-dev libx11-xcb-dev libxcb-keysyms1-dev ca-certificates patch xz-utils cmake \
 llvm-15-dev libclang-15-dev libclang-cpp15-dev libclc-15-dev libclc-15 libllvmspirvlib-15-dev \
 spirv-tools spirv-headers glslang-tools libvulkan-dev libvulkan-dev:i386 \
 libdrm-dev:i386 libexpat1-dev:i386 libzstd-dev:i386 zlib1g-dev:i386 libx11-dev:i386 libxext-dev:i386 \
 libxfixes-dev:i386 libxrandr-dev:i386 libxshmfence-dev:i386 libxcb-shm0-dev:i386 libxcb-xfixes0-dev:i386 \
 libxcb-xinput-dev:i386 libxxf86vm-dev:i386 libxcb-glx0-dev:i386 libxcb-dri2-0-dev:i386 \
 libxcb-dri3-dev:i386 libxcb-present-dev:i386 libxcb-sync-dev:i386 libxcb-randr0-dev:i386 \
 libglvnd-dev:i386 libelf-dev:i386 libudev-dev:i386 libgtest-dev:i386 libx11-xcb-dev:i386 \
 libxcb-keysyms1-dev:i386 libwayland-dev:i386 libwayland-egl-backend-dev:i386
python3 -m venv --system-site-packages /opt/build-tools
/opt/build-tools/bin/pip install meson==1.8.5
export PATH=/opt/build-tools/bin:$PATH
src=/opt/qy0z-build-sources
mkdir -p "$src"
python3 /project/scripts/fetch_sources.py spirv-tools "$src/spirv-tools"
python3 /project/scripts/fetch_sources.py spirv-headers "$src/spirv-tools/external/spirv-headers"
cmake -S "$src/spirv-tools" -B "$src/spirv-tools-build" -DCMAKE_BUILD_TYPE=Release \
 -DSPIRV_SKIP_TESTS=ON -DSPIRV_SKIP_EXECUTABLES=ON -DBUILD_SHARED_LIBS=OFF \
 -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_INSTALL_PREFIX=/opt/spirv-tools
cmake --build "$src/spirv-tools-build" -j4
cmake --install "$src/spirv-tools-build"
python3 /project/scripts/fetch_sources.py glslang "$src/glslang"
cmake -S "$src/glslang" -B "$src/glslang-build" -DCMAKE_BUILD_TYPE=Release \
 -DCMAKE_INSTALL_PREFIX=/opt/glslang -DENABLE_OPT=OFF -DBUILD_TESTING=OFF -DENABLE_CTEST=OFF
cmake --build "$src/glslang-build" -j4
cmake --install "$src/glslang-build"
python3 /project/scripts/fetch_sources.py wayland-protocols "$src/wayland-protocols"
meson setup "$src/wayland-protocols-build" "$src/wayland-protocols" \
 --prefix=/opt/wayland-protocols -Dtests=false
meson install -C "$src/wayland-protocols-build"
