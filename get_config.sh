#!/usr/bin/env bash
repo_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

get_debian_vers_from_pkg_repo() {
    debian_version_line=$(grep -m1 'debian_ref=' "$repo_dir/prepare_source")
    echo "${debian_version_line#*=}" | tr -d '"'
    }

get_vers_orig_from_pkg_repo() {
    version_orig_line=$(grep -m1 'version_orig=' "$repo_dir/prepare_source")
    echo "${version_orig_line#*=}" | tr -d '"'
    }

deb_version=$(get_debian_vers_from_pkg_repo)
version_orig=$(get_vers_orig_from_pkg_repo)

arch=$(dpkg --print-architecture 2>/dev/null)


apt-get install -y --no-install-recommends quilt flex bison build-essential gcc-14 make fakeroot libncurses-dev kernel-wedge python3-jinja2 python3-dacite wget gpgv

apt-get remove --purge sqopv -y

mkdir -p /tmp

cd /tmp

git clone https://salsa.debian.org/kernel-team/linux.git
cd linux
git checkout $deb_version


uscan -v --download-version="$version_orig"
git clean -fdx


mkdir /tmp/src

xz -d < ../*.orig.tar.* | tar --extract --strip-components 1 --directory "/tmp/src"

cp -r debian "/tmp/src/"

cd /tmp/src

cp $repo_dir/fixes_debian/series.patch /tmp/src/

patch -p1 < series.patch

export QUILT_PATCHES=debian/patches
quilt pop -a || true
quilt push -a

fakeroot make -f debian/rules debian/control

make -f debian/rules.gen setup_"$arch"_none_cloud-$arch
make -f debian/rules.gen setup_"$arch"_none_$arch

cp debian/build/build_"$arch"_none_cloud-$arch/.config $repo_dir/config_"$arch"_none_cloud-$arch
cp debian/build/build_"$arch"_none_$arch/.config $repo_dir/config_"$arch"_none_$arch

fakeroot make -f debian/rules clean
rm -rf "debian/config"
cp -r $repo_dir/config "debian/"

fakeroot make -f debian/rules debian/control

make -f debian/rules.gen setup_"$arch"_none_cloud-$arch
make -f debian/rules.gen setup_"$arch"_none_$arch

cp debian/build/build_"$arch"_none_cloud-$arch/.config $repo_dir/config_gl_"$arch"_none_cloud-$arch
cp debian/build/build_"$arch"_none_$arch/.config $repo_dir/config_gl_"$arch"_none_$arch