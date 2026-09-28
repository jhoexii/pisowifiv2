#!/usr/bin/env bash
set -euo pipefail

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARMBIAN_DIR="${ARMBIAN_DIR:-$KIT_DIR/armbian-build}"

if [[ -f "$KIT_DIR/build.env" ]]; then
  set -a
  source "$KIT_DIR/build.env"
  set +a
fi

if [[ ! -d "$ARMBIAN_DIR/.git" ]]; then
  git clone --depth=1 https://github.com/armbian/build "$ARMBIAN_DIR"
fi

rm -rf "$ARMBIAN_DIR/userpatches"
cp -a "$KIT_DIR/userpatches" "$ARMBIAN_DIR/userpatches"

cd "$ARMBIAN_DIR"
sudo ./compile.sh requirements
sudo chown -R "$(id -u):$(id -g)" .
./compile.sh pisowifi \
  BOARD=orangepizero3 \
  RELEASE=trixie \
  BRANCH=current \
  BUILD_DESKTOP=no \
  BUILD_MINIMAL=yes \
  KERNEL_CONFIGURE=no \
  EXTRAVERSION="-pisowifi"

echo
printf 'Image(s) are in: %s\n' "$ARMBIAN_DIR/output/images/"
