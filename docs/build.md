# Build the source patches

The reference builds used Mesa 26.0.8, with release version `26.0.8-qy0z.1`.
Archive SHA256: `caf1c0061a68e88dfa74967a7e780c0e85d65b6c4e334cd69095a5dc54ad78bc`.

Use a Linux x86-64 Docker host. Cross-architecture emulation on an ARM Mac is not
a validated performance or GPU test environment. Build containers need no GPU,
privileged mode, host root mount or production configuration.

## Reference-compatible recipes

The two Dockerfiles adapt the recorded package/build commands into reusable
recipes. They have static/unit/patch checks; a full clean-image rebuild of these
newly packaged recipes is not yet a published CI result. Package repositories
are not frozen snapshots. Read a failed dependency/configuration check rather
than replacing it with an unchecked download or silently dropping assertions.

Ubuntu 26.04 x86-64 (the compatible family for the tested streaming container):

```sh
mkdir -p work out
docker build -f containers/Dockerfile.ubuntu26 -t qy0z-builder:ubuntu26 .
docker run --rm --cpus=4 --memory=6g \
   -v "$PWD/work:/work" -v "$PWD/out:/out" qy0z-builder:ubuntu26 64
```

Debian 12 x86-64, with a 32-bit build for compatible Steam containers:

```sh
mkdir -p work out
docker build -f containers/Dockerfile.debian12 -t qy0z-builder:debian12 .
docker run --rm --cpus=4 --memory=6g \
   -v "$PWD/work:/work" -v "$PWD/out:/out" qy0z-builder:debian12 64
docker run --rm --cpus=4 --memory=6g \
   -v "$PWD/work:/work" -v "$PWD/out:/out" qy0z-builder:debian12 32
```

Use separate `work`/`out` directories for different distribution/toolchain builds.
The 32-bit build reuses the native `mesa_clc`/`vtn_bindgen2` from its own preceding
Debian 64-bit build. It does not require 32-bit LLVM compilation tools.
The selected native and i386 flags follow the reference recipe.

Only driver/install targets and six relevant ISL regression executables are
compiled; unrelated upstream shader test executables are not built. This does
not mean the complete Mesa test suite passed. Regression results appear in
`work/build64/meson-logs` and `work/build32/meson-logs`.

The staged runtime is `out/opt/qy0z-mesa`. Preserve architecture-specific Vulkan
ICDs (`intel_icd.x86_64.json` and `intel_icd.i686.json`), which refer to their
absolute library paths under `/opt/qy0z-mesa`. They may be installed into a
matching container by a read-only bind mount to that same prefix.

Do not overwrite host libraries with the Ubuntu build on Debian 12. Do not copy
bare libraries between arbitrary containers without checking runtime dependencies.
The Debian reference runtime was tested on a Debian 12 host and Debian 13 Steam
image; that is not a universal glibc/musl ABI promise. Alpine/musl is not supported.

## Local package checks

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
python3 scripts/fetch_sources.py mesa /tmp/mesa-qy0z-check
patch --dry-run -d /tmp/mesa-qy0z-check -p1 < patches/0001-adlp-a0-disable-ccs.patch
```

Apply 0001 before checking/applying 0002. The build script applies both to a fresh
verified source tree. It refuses an existing source directory without its patch
marker; it never deletes or replaces an existing source tree automatically.
No build script installs to the running host or reboots it.

## Compile the C probes (no GPU work during compilation)

Inside a builder with GL/EGL/Vulkan development libraries:

```sh
sh scripts/build-probes.sh 64
# Debian multilib builder only:
sh scripts/build-probes.sh 32
```

The stock-Iris probe intentionally expects the recorded Mesa 25.0.7 fallback
and `INTEL_DEBUG=noccs`. Native custom-Iris probes expect `qy0z.1`; Steam Zink
probes require the patched ANV library in their process mappings. Choose the
probe matching the documented route rather than deleting a failed assertion.
The Vulkan probe takes the compiled `compute.spv` path as its single argument.
GLX probes require an existing X display and appropriate authentication.
