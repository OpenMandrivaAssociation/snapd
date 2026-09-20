# This rpm is based on one supplied in the packaging directory of the snapd sources.
# All the go language modules are included in the sources. The anount of effort required 
# to package them all is huge this a tar archive containing the go binaries is provided, When updating this package 
# these go binaries must be downloaded alon with the main source distributiom
# Neither selinux or apparmour are ebabled for this build.
#ImORTANT NOTE: Do not remove the glibc-debuginfo package as this is required for the tests.


%bcond vendorized 1


# Classic snaps currently require a symlink to

%bcond snap_symlink 0


# A switch to allow building the package with support for testkeys which
# are used for the spread test suite of snapd.
%bcond test_keys 0

%global with_devel 0
%global with_debug 0
%global with_check 0
%global with_unit_test 0
#%%global with_test_keys 0
%global with_selinux 0

# For the moment, we don't support all golang arches...
%global with_goarches 0

# Set if multilib is enabled for supported arches
%ifarch x86_64 znver1 aarch64 %{power64} s390x
%global with_multilib 1
%endif

# Set if valgrind is to be run
%ifnarch ppc64le
%global with_valgrind 0
%endif

%if ! %{with vendorized}
%global with_bundled 0
%else
%global with_bundled 1
%endif

%if %{with test_keys}
%global with_test_keys 1
%else
%global with_test_keys 0
%endif

%if 0%{?with_debug}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package   %{nil}
%endif

%global provider        github
%global provider_tld    com
%global project         snapcore
%global repo            snapd
# https://github.com/snapcore/snapd
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path     %{provider_prefix}

%global snappy_svcs      snapd.service snapd.socket snapd.seeded.service snapd.mounts.target snapd.mounts-pre.target
%global snappy_user_svcs snapd.session-agent.service snapd.session-agent.socket


# Applied via %caps in %files. cap_sys_resource needed since 2.77 (ebpf memlock).
# No cap_setuid/setgid: those are cgroup-v1 only.
%global snap_confine_caps cap_chown,cap_dac_override,cap_dac_read_search,cap_fowner,cap_sys_chroot,cap_sys_ptrace,cap_sys_admin,cap_sys_resource=p


# Until we have a way to add more extldflags to gobuild macro...
# Always use external linking when building static binaries.
# OpenMandriva does not ship the go-build macros
%define gobuild_static(o:) go build -buildmode pie -compiler gc -tags="rpm_crashtraceback ${BUILDTAGS:-}" -ldflags "-B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n') -linkmode external -extldflags '%__global_ldflags -static'" -a -v %{?**};
%define gobuild(o:) go build -buildmode pie -compiler gc -tags="rpm_crashtraceback ${BUILDTAGS:-}" -ldflags "-B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n') -linkmode external -extldflags '%__global_ldflags'" -a -v %{?**};
%define gobuild(o:) go build -compiler gc -tags="rpm_crashtraceback ${BUILDTAGS:-}" -ldflags "-B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n') -linkmode external -extldflags '%__global_ldflags'" -a -v %{?**};
%define gotest() go test -compiler gc %{?**};


# Compat path macros
%{!?_environmentdir: %global _environmentdir %{_prefix}/lib/environment.d}
%{!?_systemdgeneratordir: %global _systemdgeneratordir %{_prefix}/lib/systemd/system-generators}
%{!?_systemd_system_env_generator_dir: %global _systemd_system_env_generator_dir %{_prefix}/lib/systemd/system-environment-generators}
%{!?_tmpfilesdir: %global _tmpfilesdir %{_prefix}/lib/tmpfiles.d}

# Fedora selinux-policy includes 'map' permission on a 'file' class. However,
# Amazon Linux 2 does not have the updated policy containing the fix for
# https://bugzilla.redhat.com/show_bug.cgi?id=1574383.
# For now disable SELinux on Amazon Linux 2 until it's fixed.
%global with_selinux 0


Name:           snapd
Version:        2.77.1
Release:        2
Summary:        A transactional software package manager
License:        GPL-3.0-only
Group:          System/Packaging
URL:            https://%{provider_prefix}
Source0:        https://%{provider_prefix}/releases/download/%{version}/%{name}_%{version}.no-vendor.tar.xz
Source1:        https://%{provider_prefix}/releases/download/%{version}/%{name}_%{version}.only-vendor.tar.xz

%if 0%{?with_goarches}
# e.g. el6 has ppc64 arch without gcc-go, so EA tag is required
ExclusiveArch:  %{?go_arches:%{go_arches}}%{!?go_arches:%{ix86} x86_64 %{arm}}
%else
# Verified arches from snapd upstream
ExclusiveArch:  %{ix86} x86_64 znver1 %{arm} aarch64 ppc64le s390x
%endif

# If go_compiler is not set to 1, there is no virtual provide. Use golang instead.
BuildRequires: make
BuildRequires:  %{?go_compiler:compiler(go-compiler)}%{!?go_compiler:golang >= 1.9}
BuildRequires:  systemd
%{?systemd_requires}
BuildRequires:	glibc-debuginfo

Requires:       snap-confine%{?_isa} = %{version}-%{release}
Requires:       squashfs-tools

# bash-completion owns /usr/share/bash-completion/completions
Requires:       bash-completion

#%if 0%{?with_selinux}
# Force the SELinux module to be installed
#Requires:       %{name}-selinux = %{version}-%{release}
#%endif

%if ! 0%{?with_bundled}
BuildRequires: golang(go.etcd.io/bbolt)
BuildRequires: golang(github.com/bmatcuk/doublestar/v4)
BuildRequires: golang(github.com/coreos/go-systemd/activation)
BuildRequires: golang(github.com/godbus/dbus/v5)
BuildRequires: golang(github.com/godbus/dbus/v5/introspect)
BuildRequires: golang(github.com/gorilla/mux)
BuildRequires: golang(github.com/jessevdk/go-flags)
BuildRequires: golang(github.com/juju/ratelimit)
BuildRequires: golang(github.com/kr/pretty)
BuildRequires: golang(github.com/kr/text)
BuildRequires: golang(github.com/mvo5/goconfigparser)
BuildRequires: golang(github.com/seccomp/libseccomp-golang)
BuildRequires: golang(github.com/snapcore/go-gettext)
BuildRequires: golang(golang.org/x/crypto/openpgp/armor)
BuildRequires: golang(golang.org/x/crypto/openpgp/packet)
BuildRequires: golang(golang.org/x/crypto/sha3)
BuildRequires: golang(golang.org/x/crypto/ssh/terminal)
BuildRequires: golang(golang.org/x/xerrors)
BuildRequires: golang(golang.org/x/xerrors/internal)
BuildRequires: golang(gopkg.in/check.v1)
BuildRequires: golang(gopkg.in/macaroon.v1)
BuildRequires: golang(gopkg.in/mgo.v2/bson)
BuildRequires: golang(gopkg.in/retry.v1)
BuildRequires: golang(gopkg.in/tomb.v2)
BuildRequires: golang(gopkg.in/yaml.v2)
BuildRequires: golang(gopkg.in/yaml.v3)
%endif

%description
Snappy is a modern, cross-distribution, transactional package manager
designed for working with self-contained, immutable packages.

%package -n snap-confine
Summary:        Confinement system for snap applications
License:        GPL-3.0-only
BuildRequires:  autoconf
BuildRequires:  autoconf-archive
BuildRequires:  automake
BuildRequires:  make
BuildRequires:  m4
BuildRequires:  libtool
BuildRequires:  gcc
BuildRequires:  gettext
BuildRequires:  gnupg
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(libcap)
BuildRequires:  pkgconfig(libseccomp)
%if 0%{?with_selinux}
BuildRequires:  pkgconfig(libselinux)
%endif
BuildRequires:  pkgconfig(libudev)
BuildRequires:  pkgconfig(systemd)
BuildRequires:  xfsprogs-devel
BuildRequires:  glibc-static-devel
%if ! 0%{?rhel}
BuildRequires:  lib64seccomp2-static
%endif
%if 0%{?with_valgrind}
BuildRequires:  valgrind
%endif
BuildRequires:  %{_bindir}/rst2man
%if 0%{?fedora} && ! 0%{?amzn2023}
# AL2023 does not have shellcheck
# ShellCheck in EPEL is too old...
BuildRequires:  %{_bindir}/shellcheck
%endif

# Ensures older version from split packaging is replaced
Obsoletes:      snap-confine < 2.19

%description -n snap-confine
This package is used internally by snapd to apply confinement to
the started snap applications.

%if 0%{?with_selinux}
%package selinux
Summary:        SELinux module for snapd
License:        GPL-2.0-or-later
BuildArch:      noarch
BuildRequires:  selinux-policy
BuildRequires:  selinux-policy-devel
BuildRequires:  make
%{?selinux_requires}

%description selinux
This package provides the SELinux policy module to ensure snapd
runs properly under an environment with SELinux enabled.
%endif

%if 0%{?with_devel}
%package devel
Summary:       Development files for %{name}
BuildArch:     noarch

%if 0%{?with_check} && ! 0%{?with_bundled}
%endif

%if ! 0%{?with_bundled}
Requires:      golang(github.com/bmatcuk/doublestar/v4)
Requires:      golang(github.com/coreos/go-systemd/activation)
Requires:      golang(github.com/godbus/dbus/v5)
Requires:      golang(github.com/godbus/dbus/v5/introspect)
Requires:      golang(github.com/gorilla/mux)
Requires:      golang(github.com/jessevdk/go-flags)
Requires:      golang(github.com/juju/ratelimit)
Requires:      golang(github.com/kr/pretty)
Requires:      golang(github.com/kr/text)
Requires:      golang(github.com/mattn/go-runewidth)
Requires:      golang(github.com/mvo5/goconfigparser)
Requires:      golang(github.com/rivo/uniseg)
Requires:      golang(github.com/seccomp/libseccomp-golang)
Requires:      golang(github.com/snapcore/go-gettext)
Requires:      golang(go.etcd.io/bbolt)
Requires:      golang(golang.org/x/crypto/openpgp/armor)
Requires:      golang(golang.org/x/crypto/openpgp/packet)
Requires:      golang(golang.org/x/crypto/sha3)
Requires:      golang(golang.org/x/crypto/ssh/terminal)
Requires:      golang(golang.org/x/xerrors)
Requires:      golang(golang.org/x/xerrors/internal)
Requires:      golang(gopkg.in/check.v1)
Requires:      golang(gopkg.in/macaroon.v1)
Requires:      golang(gopkg.in/mgo.v2/bson)
Requires:      golang(gopkg.in/retry.v1)
Requires:      golang(gopkg.in/tomb.v2)
Requires:      golang(gopkg.in/yaml.v2)
Requires:      golang(gopkg.in/yaml.v3)
%else
# These Provides are unversioned because the sources in
# the bundled tarball are unversioned (they go by git commit)
# *sigh*... I hate golang...
Provides:      bundled(golang(github.com/bmatcuk/doublestar/v4))
Provides:      bundled(golang(github.com/coreos/go-systemd/activation))
Provides:      bundled(golang(github.com/godbus/dbus/v5))
Provides:      bundled(golang(github.com/godbus/dbus/v5/introspect))
Provides:      bundled(golang(github.com/gorilla/mux))
Provides:      bundled(golang(github.com/jessevdk/go-flags))
Provides:      bundled(golang(github.com/juju/ratelimit))
Provides:      bundled(golang(github.com/kr/pretty))
Provides:      bundled(golang(github.com/kr/text))
Provides:      bundled(golang(github.com/mattn/go-runewidth))
Provides:      bundled(golang(github.com/mvo5/goconfigparser))
Provides:      bundled(golang(github.com/rivo/uniseg))
Provides:      bundled(golang(github.com/seccomp/libseccomp-golang))
Provides:      bundled(golang(github.com/snapcore/go-gettext))
Provides:      bundled(golang(go.etcd.io/bbolt))
Provides:      bundled(golang(golang.org/x/crypto/openpgp/armor))
Provides:      bundled(golang(golang.org/x/crypto/openpgp/packet))
Provides:      bundled(golang(golang.org/x/crypto/sha3))
Provides:      bundled(golang(golang.org/x/crypto/ssh/terminal))
Provides:      bundled(golang(golang.org/x/xerrors))
Provides:      bundled(golang(golang.org/x/xerrors/internal))
Provides:      bundled(golang(gopkg.in/check.v1))
Provides:      bundled(golang(gopkg.in/macaroon.v1))
Provides:      bundled(golang(gopkg.in/mgo.v2/bson))
Provides:      bundled(golang(gopkg.in/retry.v1))
Provides:      bundled(golang(gopkg.in/tomb.v2))
Provides:      bundled(golang(gopkg.in/yaml.v2))
Provides:      bundled(golang(gopkg.in/yaml.v3))
%endif

# Generated by gofed
Provides:      golang(%{import_path}/advisor) = %{version}-%{release}
Provides:      golang(%{import_path}/arch) = %{version}-%{release}
Provides:      golang(%{import_path}/asserts) = %{version}-%{release}
Provides:      golang(%{import_path}/asserts/assertstest) = %{version}-%{release}
Provides:      golang(%{import_path}/asserts/internal) = %{version}-%{release}
Provides:      golang(%{import_path}/asserts/signtool) = %{version}-%{release}
Provides:      golang(%{import_path}/asserts/snapasserts) = %{version}-%{release}
Provides:      golang(%{import_path}/asserts/sysdb) = %{version}-%{release}
Provides:      golang(%{import_path}/asserts/systestkeys) = %{version}-%{release}
Provides:      golang(%{import_path}/boot) = %{version}-%{release}
Provides:      golang(%{import_path}/boot/boottest) = %{version}-%{release}
Provides:      golang(%{import_path}/bootloader) = %{version}-%{release}
Provides:      golang(%{import_path}/bootloader/androidbootenv) = %{version}-%{release}
Provides:      golang(%{import_path}/bootloader/assets) = %{version}-%{release}
Provides:      golang(%{import_path}/bootloader/assets/genasset) = %{version}-%{release}
Provides:      golang(%{import_path}/bootloader/bootloadertest) = %{version}-%{release}
Provides:      golang(%{import_path}/bootloader/efi) = %{version}-%{release}
Provides:      golang(%{import_path}/bootloader/grubenv) = %{version}-%{release}
Provides:      golang(%{import_path}/bootloader/lkenv) = %{version}-%{release}
Provides:      golang(%{import_path}/bootloader/ubootenv) = %{version}-%{release}
Provides:      golang(%{import_path}/client) = %{version}-%{release}
Provides:      golang(%{import_path}/client/clientutil) = %{version}-%{release}
Provides:      golang(%{import_path}/cmd/snap) = %{version}-%{release}
Provides:      golang(%{import_path}/cmd/snap-bootstrap) = %{version}-%{release}
Provides:      golang(%{import_path}/cmd/snap-bootstrap/triggerwatch) = %{version}-%{release}
Provides:      golang(%{import_path}/cmd/snap-exec) = %{version}-%{release}
Provides:      golang(%{import_path}/cmd/snap-failure) = %{version}-%{release}
Provides:      golang(%{import_path}/cmd/snap-preseed) = %{version}-%{release}
Provides:      golang(%{import_path}/cmd/snap-recovery-chooser) = %{version}-%{release}
Provides:      golang(%{import_path}/cmd/snap-repair) = %{version}-%{release}
Provides:      golang(%{import_path}/cmd/snap-seccomp) = %{version}-%{release}
Provides:      golang(%{import_path}/cmd/snap-seccomp/syscalls) = %{version}-%{release}
Provides:      golang(%{import_path}/cmd/snap-update-ns) = %{version}-%{release}
Provides:      golang(%{import_path}/cmd/snapctl) = %{version}-%{release}
Provides:      golang(%{import_path}/cmd/snapd) = %{version}-%{release}
Provides:      golang(%{import_path}/cmd/snaplock) = %{version}-%{release}
Provides:      golang(%{import_path}/cmd/snaplock/runinhibit) = %{version}-%{release}
Provides:      golang(%{import_path}/daemon) = %{version}-%{release}
Provides:      golang(%{import_path}/dbusutil) = %{version}-%{release}
Provides:      golang(%{import_path}/dbusutil/dbustest) = %{version}-%{release}
Provides:      golang(%{import_path}/desktop/notification) = %{version}-%{release}
Provides:      golang(%{import_path}/desktop/notification/notificationtest) = %{version}-%{release}
Provides:      golang(%{import_path}/dirs) = %{version}-%{release}
Provides:      golang(%{import_path}/docs) = %{version}-%{release}
Provides:      golang(%{import_path}/features) = %{version}-%{release}
Provides:      golang(%{import_path}/gadget) = %{version}-%{release}
Provides:      golang(%{import_path}/gadget/edition) = %{version}-%{release}
Provides:      golang(%{import_path}/gadget/install) = %{version}-%{release}
Provides:      golang(%{import_path}/gadget/internal) = %{version}-%{release}
Provides:      golang(%{import_path}/gadget/quantity) = %{version}-%{release}
Provides:      golang(%{import_path}/httputil) = %{version}-%{release}
Provides:      golang(%{import_path}/i18n) = %{version}-%{release}
Provides:      golang(%{import_path}/i18n/xgettext-go) = %{version}-%{release}
Provides:      golang(%{import_path}/image) = %{version}-%{release}
Provides:      golang(%{import_path}/interfaces) = %{version}-%{release}
Provides:      golang(%{import_path}/interfaces/apparmor) = %{version}-%{release}
Provides:      golang(%{import_path}/interfaces/backends) = %{version}-%{release}
Provides:      golang(%{import_path}/interfaces/builtin) = %{version}-%{release}
Provides:      golang(%{import_path}/interfaces/dbus) = %{version}-%{release}
Provides:      golang(%{import_path}/interfaces/hotplug) = %{version}-%{release}
Provides:      golang(%{import_path}/interfaces/ifacetest) = %{version}-%{release}
Provides:      golang(%{import_path}/interfaces/kmod) = %{version}-%{release}
Provides:      golang(%{import_path}/interfaces/mount) = %{version}-%{release}
Provides:      golang(%{import_path}/interfaces/policy) = %{version}-%{release}
Provides:      golang(%{import_path}/interfaces/seccomp) = %{version}-%{release}
Provides:      golang(%{import_path}/interfaces/systemd) = %{version}-%{release}
Provides:      golang(%{import_path}/interfaces/udev) = %{version}-%{release}
Provides:      golang(%{import_path}/interfaces/utils) = %{version}-%{release}
Provides:      golang(%{import_path}/jsonutil) = %{version}-%{release}
Provides:      golang(%{import_path}/jsonutil/safejson) = %{version}-%{release}
Provides:      golang(%{import_path}/kernel) = %{version}-%{release}
Provides:      golang(%{import_path}/logger) = %{version}-%{release}
Provides:      golang(%{import_path}/metautil) = %{version}-%{release}
Provides:      golang(%{import_path}/netutil) = %{version}-%{release}
Provides:      golang(%{import_path}/osutil) = %{version}-%{release}
Provides:      golang(%{import_path}/osutil/disks) = %{version}-%{release}
Provides:      golang(%{import_path}/osutil/mount) = %{version}-%{release}
Provides:      golang(%{import_path}/osutil/squashfs) = %{version}-%{release}
Provides:      golang(%{import_path}/osutil/strace) = %{version}-%{release}
Provides:      golang(%{import_path}/osutil/sys) = %{version}-%{release}
Provides:      golang(%{import_path}/osutil/udev/crawler) = %{version}-%{release}
Provides:      golang(%{import_path}/osutil/udev/netlink) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/assertstate) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/assertstate/assertstatetest) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/auth) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/cmdstate) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/configstate) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/configstate/config) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/configstate/configcore) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/configstate/proxyconf) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/configstate/settings) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/devicestate) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/devicestate/devicestatetest) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/devicestate/fde) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/devicestate/internal) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/healthstate) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/hookstate) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/hookstate/ctlcmd) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/hookstate/hooktest) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/ifacestate) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/ifacestate/ifacerepo) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/ifacestate/udevmonitor) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/patch) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/servicestate) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/snapshotstate) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/snapshotstate/backend) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/snapstate) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/snapstate/backend) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/snapstate/policy) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/snapstate/snapstatetest) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/standby) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/state) = %{version}-%{release}
Provides:      golang(%{import_path}/overlord/storecontext) = %{version}-%{release}
Provides:      golang(%{import_path}/polkit) = %{version}-%{release}
Provides:      golang(%{import_path}/progress) = %{version}-%{release}
Provides:      golang(%{import_path}/progress/progresstest) = %{version}-%{release}
Provides:      golang(%{import_path}/randutil) = %{version}-%{release}
Provides:      golang(%{import_path}/release) = %{version}-%{release}
Provides:      golang(%{import_path}/sandbox) = %{version}-%{release}
Provides:      golang(%{import_path}/sandbox/apparmor) = %{version}-%{release}
Provides:      golang(%{import_path}/sandbox/cgroup) = %{version}-%{release}
Provides:      golang(%{import_path}/sandbox/seccomp) = %{version}-%{release}
Provides:      golang(%{import_path}/sandbox/selinux) = %{version}-%{release}
Provides:      golang(%{import_path}/sanity) = %{version}-%{release}
Provides:      golang(%{import_path}/secboot) = %{version}-%{release}
Provides:      golang(%{import_path}/seed) = %{version}-%{release}
Provides:      golang(%{import_path}/seed/internal) = %{version}-%{release}
Provides:      golang(%{import_path}/seed/seedtest) = %{version}-%{release}
Provides:      golang(%{import_path}/seed/seedwriter) = %{version}-%{release}
Provides:      golang(%{import_path}/snap) = %{version}-%{release}
Provides:      golang(%{import_path}/snap/channel) = %{version}-%{release}
Provides:      golang(%{import_path}/snap/internal) = %{version}-%{release}
Provides:      golang(%{import_path}/snap/naming) = %{version}-%{release}
Provides:      golang(%{import_path}/snap/pack) = %{version}-%{release}
Provides:      golang(%{import_path}/snap/snapdir) = %{version}-%{release}
Provides:      golang(%{import_path}/snap/snapenv) = %{version}-%{release}
Provides:      golang(%{import_path}/snap/snapfile) = %{version}-%{release}
Provides:      golang(%{import_path}/snap/snaptest) = %{version}-%{release}
Provides:      golang(%{import_path}/snap/squashfs) = %{version}-%{release}
Provides:      golang(%{import_path}/snapdenv) = %{version}-%{release}
Provides:      golang(%{import_path}/snapdtool) = %{version}-%{release}
Provides:      golang(%{import_path}/spdx) = %{version}-%{release}
Provides:      golang(%{import_path}/store) = %{version}-%{release}
Provides:      golang(%{import_path}/store/storetest) = %{version}-%{release}
Provides:      golang(%{import_path}/strutil) = %{version}-%{release}
Provides:      golang(%{import_path}/strutil/chrorder) = %{version}-%{release}
Provides:      golang(%{import_path}/strutil/quantity) = %{version}-%{release}
Provides:      golang(%{import_path}/strutil/shlex) = %{version}-%{release}
Provides:      golang(%{import_path}/sysconfig) = %{version}-%{release}
Provides:      golang(%{import_path}/systemd) = %{version}-%{release}
Provides:      golang(%{import_path}/testutil) = %{version}-%{release}
Provides:      golang(%{import_path}/timeout) = %{version}-%{release}
Provides:      golang(%{import_path}/timeutil) = %{version}-%{release}
Provides:      golang(%{import_path}/timings) = %{version}-%{release}
Provides:      golang(%{import_path}/usersession/agent) = %{version}-%{release}
Provides:      golang(%{import_path}/usersession/autostart) = %{version}-%{release}
Provides:      golang(%{import_path}/usersession/client) = %{version}-%{release}
Provides:      golang(%{import_path}/usersession/userd) = %{version}-%{release}
Provides:      golang(%{import_path}/usersession/userd/ui) = %{version}-%{release}
Provides:      golang(%{import_path}/usersession/xdgopenproxy) = %{version}-%{release}
Provides:      golang(%{import_path}/wrappers) = %{version}-%{release}
Provides:      golang(%{import_path}/x11) = %{version}-%{release}

%description devel
This package contains library source intended for
building other packages which use import path with
%{import_path} prefix.
%endif

%if 0%{?with_unit_test} && 0%{?with_devel}
%package unit-test-devel
Summary:         Unit tests for %{name} package

%if 0%{?with_check}
#Here comes all BuildRequires: PACKAGE the unit tests
#in %%check section need for running
%endif

# test subpackage tests code from devel subpackage
Requires:        %{name}-devel = %{version}-%{release}

%description unit-test-devel
This package contains unit tests for project
providing packages with %{import_path} prefix.
%endif

%prep
%if ! 0%{?with_bundled}
%setup -q
# Ensure there's no bundled stuff accidentally leaking in...
rm -rf vendor
%else
# Extract each tarball properly
%setup -q -D -b 1
%endif
# Apply patches
%autopatch -p1


%build

%if ! 0%{?with_bundled}
# We don't need the snapcore fork for bolt - it is just a fix on ppc
sed -e "s:github.com/snapcore/bolt:github.com/boltdb/bolt:g" -i advisor/*.go
%endif

%if 0%{?rhel} >= 7
    # since RH Developer tools 2018.4 (and later releases),
    # the go-toolset module is built with FIPS compliance that
    # defaults to using libcrypto.so which gets loaded at runtime via dlopen(),
    # disable that functionality for statically built binaries
    EXTRA_TAGS="${EXTRA_TAGS} no_openssl"
%endif

# Generate snapd.defines.mk, this file is included by snapd.mk. It contains a
# number of variable definitions that are set based on their RPM equivalents.
# Since we can apply any conditional overrides here in the spec file we can
# maintain one consistent set of variables across the spec and makefile worlds.
cat >snapd.defines.mk <<__DEFINES__
# This file is generated by Fedora's snapd.spec
# Directory variables.
prefix = %{_prefix}
bindir = %{_bindir}
sbindir = %{_sbindir}
libexecdir = %{_libexecdir}
mandir = %{_mandir}
datadir = %{_datadir}
localstatedir = %{_localstatedir}
sharedstatedir = %{_localstatedir}/lib
unitdir = %{_unitdir}
builddir = %{_builddir}
# Build configuration
with_core_bits = 0
with_alt_snap_mount_dir = 0
with_apparmor = 1
with_testkeys = %{with_test_keys}
with_vendor = %{with_bundled}
with_static_pie = 0
# follow what %%gobuild does
EXTRA_GO_BUILD_FLAGS = -v -x -compiler gc
EXTRA_GO_LDFLAGS = -linkmode external -extldflags '%__global_ldflags'
EXTRA_GO_STATIC_LDFLAGS = -linkmode external -extldflags '%__global_ldflags -static'
EXTRA_GO_BUILD_TAGS = rpm_crashtraceback $EXTRA_TAGS
__DEFINES__

# Generate version files
DPKG_PARSECHANGELOG="" ./mkversion.sh "%{version}-%{release}"

# Build SELinux policy module
%if 0%{?with_selinux}
(
%if 0%{?rhel} == 7
    M4PARAM='-D distro_rhel7'
%endif
%if 0%{?rhel} == 7 || 0%{?rhel} == 8
    # RHEL7, RHEL8 are missing the BPF interfaces from their reference policy
    M4PARAM="$M4PARAM -D no_bpf"
%endif
    # Build SELinux module
    cd ./data/selinux
    # pass M4PARAM in env instead of as an override, so that make can still
    # manipulate it freely, for more details see:
    # https://www.gnu.org/software/make/manual/html_node/Override-Directive.html
    M4PARAM="$M4PARAM" make SHARE="%{_datadir}" TARGETS="snappy"
)
%endif

# Build snap-confine
pushd ./cmd
autoreconf --force --install --verbose
# FIXME: add --enable-caps-over-setuid as soon as possible (setuid discouraged!)
./configure \
    --disable-apparmor \
%if 0%{?with_selinux}
    --enable-selinux \
%endif
%if 0%{?rhel} == 7 || 0%{?amzn2} == 1
    --disable-bpf \
%endif
     --prefix=/usr --sysconfdir=/etc --localstatedir=/var \
    --libexecdir=%{_libexecdir}/snapd/ \
    --with-snap-mount-dir=%{_localstatedir}/lib/snapd/snap 
#    --prefix=/usr \
#    --sharedstatedir=/usr/com/snapd
#    --enable-nvidia-biarch 
#    --enable-merged-usr \
#    %{?with_multilib:--with-32bit-libdir=%{_prefix}/lib} \
%make_build %{!?with_valgrind:HAVE_VALGRIND=}
popd

# Build snap, snapd and other tools
%make_build -f packaging/snapd.mk \
            SNAPD_DEFINES_DIR=$PWD \
            all

# Build systemd units, dbus services, and env files
pushd ./data
make BINDIR="%{_bindir}" LIBEXECDIR="%{_libexecdir}" DATADIR="%{_datadir}" \
     SYSTEMDSYSTEMUNITDIR="%{_unitdir}" \
     USE_CANONICAL_SNAP_MOUNT_DIR=true \
     USE_ALT_SNAP_MOUNT_DIR=false \
     SNAPD_ENVIRONMENT_FILE="%{_sysconfdir}/sysconfig/snapd"
popd

%install
install -d -p %{buildroot}%{_bindir}
install -d -p %{buildroot}%{_libexecdir}/snapd
install -d -p %{buildroot}%{_mandir}/man8
install -d -p %{buildroot}%{_environmentdir}
install -d -p %{buildroot}%{_systemdgeneratordir}
install -d -p %{buildroot}%{_systemd_system_env_generator_dir}
install -d -p %{buildroot}%{_tmpfilesdir}
install -d -p %{buildroot}%{_unitdir}
install -d -p %{buildroot}%{_userunitdir}
install -d -p %{buildroot}%{_sysconfdir}/profile.d
install -d -p %{buildroot}%{_sysconfdir}/sysconfig
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/assertions
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/cookie
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/cgroup
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/dbus-1/services
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/dbus-1/system-services
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/desktop/applications
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/device
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/environment
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/hostfs
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/inhibit
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/lib/gl
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/lib/gl32
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/lib/glvnd
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/lib/vulkan
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/mount
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/seccomp/bpf
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/snaps
install -d -p %{buildroot}%{_localstatedir}/lib/snapd/snap/bin
install -d -p %{buildroot}%{_localstatedir}/snap
install -d -p %{buildroot}%{_localstatedir}/cache/snapd
install -d -p %{buildroot}%{_datadir}/polkit-1/actions
%if 0%{?with_selinux}
install -d -p %{buildroot}%{_datadir}/selinux/devel/include/contrib
install -d -p %{buildroot}%{_datadir}/selinux/packages
%endif

%if 0%{?with_selinux}
# Install SELinux module
install -p -m 0644 data/selinux/snappy.if %{buildroot}%{_datadir}/selinux/devel/include/contrib
install -p -m 0644 data/selinux/snappy.pp.bz2 %{buildroot}%{_datadir}/selinux/packages
%endif

# Install the "info" data file with snapd version
install -m 644 -D data/info %{buildroot}%{_libexecdir}/snapd/info

# Install bash completion for "snap"
install -m 644 -D data/completion/bash/snap %{buildroot}%{_datadir}/bash-completion/completions/snap
install -m 644 -D data/completion/bash/complete.sh %{buildroot}%{_libexecdir}/snapd
install -m 644 -D data/completion/bash/etelpmoc.sh %{buildroot}%{_libexecdir}/snapd
# Install zsh completion for "snap"
install -d -p %{buildroot}%{_datadir}/zsh/site-functions
install -m 644 -D data/completion/zsh/_snap %{buildroot}%{_datadir}/zsh/site-functions/_snap

# Install the NEWS file
install -pm 644 -D NEWS.md %{buildroot}%{_defaultdocdir}/snapd/NEWS.md

# Install snap-confine
pushd ./cmd
%make_install
# Undo the 0111 permissions, they are restored in the files section
chmod 0755 %{buildroot}%{_localstatedir}/lib/snapd/void
# We don't use AppArmor
rm -rfv %{buildroot}%{_sysconfdir}/apparmor.d
popd

# Install all systemd and dbus units, and env files
pushd ./data
%make_install BINDIR="%{_bindir}" LIBEXECDIR="%{_libexecdir}" DATADIR="%{_datadir}" \
              SYSTEMDSYSTEMUNITDIR="%{_unitdir}" SYSTEMDUSERUNITDIR="%{_userunitdir}" \
              TMPFILESDIR="%{_tmpfilesdir}" \
              USE_CANONICAL_SNAP_MOUNT_DIR=false \
              USE_ALT_SNAP_MOUNT_DIR=true \
              SNAPD_ENVIRONMENT_FILE="%{_sysconfdir}/sysconfig/snapd"
popd

# Install snap, snapd and tools
# auto-remove unnecessary files and service units
%make_install -f packaging/snapd.mk \
            SNAPD_DEFINES_DIR=$PWD \
            install

%if 0%{?rhel} == 7
# Install kernel tweaks
# See: https://access.redhat.com/articles/3128691
install -m 644 -D data/sysctl/rhel7-snap.conf %{buildroot}%{_sysctldir}/99-snap.conf
%endif

# Remove snappy core specific units
rm -fv %{buildroot}%{_unitdir}/snapd.failure.service

# Remove gpio-chardev ordering target
rm -f %{buildroot}%{_unitdir}/snapd.gpio-chardev-setup.target

# Disable re-exec by default
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
cat <<'EOF' > %{buildroot}%{_sysconfdir}/sysconfig/snapd
# Snapd daemon can reexec into the binary from the snapd snap, if
# it is newer than the version installed through distro packaging.
# Set to 1 to enable reexec. The default is 0.
#SNAP_REEXEC=0
EOF

# Create state.json and the README file to be ghosted
touch %{buildroot}%{_localstatedir}/lib/snapd/state.json
touch %{buildroot}%{_localstatedir}/lib/snapd/snap/README

# When enabled, create a symlink for /snap to point to /var/lib/snapd/snap
%if %{with snap_symlink}
ln -sr %{buildroot}%{_localstatedir}/lib/snapd/snap %{buildroot}/snap
%endif

# source codes for building projects
%if 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
echo "%%dir %%{gopath}/src/%%{import_path}/." >> devel.file-list
# find all *.go but no *_test.go files and generate devel.file-list
for file in $(find . -iname "*.go" -o -iname "*.s" \! -iname "*_test.go") ; do
    echo "%%dir %%{gopath}/src/%%{import_path}/$(dirname $file)" >> devel.file-list
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$(dirname $file)
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> devel.file-list
done
%endif

# testing files for this project
%if 0%{?with_unit_test} && 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
# find all *_test.go files and generate unit-test.file-list
for file in $(find . -iname "*_test.go"); do
    echo "%%dir %%{gopath}/src/%%{import_path}/$(dirname $file)" >> devel.file-list
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$(dirname $file)
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> unit-test-devel.file-list
done

# Install additional testdata
install -d %{buildroot}/%{gopath}/src/%{import_path}/cmd/snap/test-data/
cp -pav cmd/snap/test-data/* %{buildroot}/%{gopath}/src/%{import_path}/cmd/snap/test-data/
echo "%%{gopath}/src/%%{import_path}/cmd/snap/test-data" >> unit-test-devel.file-list
%endif

%if 0%{?with_devel}
sort -u -o devel.file-list devel.file-list
%endif

%check
for binary in snap-exec snap-update-ns snapctl; do
    ldd %{_builddir}/$binary 2>&1 | grep 'not a dynamic executable'
done

# snapd tests
%if 0%{?with_check} && 0%{?with_unit_test} && 0%{?with_devel}
%make_build -f packaging/snapd.mk \
            SNAPD_DEFINES_DIR=$PWD \
            check
%endif

# snap-confine tests (these always run!)
make -C cmd -k check
# and data files
make -C data -k check

%files
#define license tag if not already defined
%{!?_licensedir:%global license %doc}
%license COPYING
%doc README.md docs/*
/snap/README
%{_bindir}/snap
%{_bindir}/snapctl
%{_environmentdir}/990-snapd.conf
%if 0%{?rhel} == 7
%{_sysctldir}/99-snap.conf
%endif
%dir %{_libexecdir}/snapd
%{_libexecdir}/snapd/snapctl
%{_libexecdir}/snapd/snapd
%{_libexecdir}/snapd/snap-exec
%{_libexecdir}/snapd/info
%{_libexecdir}/snapd/snap-mgmt
%{_libexecdir}/snapd/snapd-apparmor
%if 0%{?with_selinux}
%{_libexecdir}/snapd/snap-mgmt-selinux
%endif
%{_mandir}/man8/snap.8*
%{_datadir}/applications/snap-handle-link.desktop
%{_datadir}/bash-completion/completions/snap
%{_libexecdir}/snapd/complete.sh
%{_libexecdir}/snapd/etelpmoc.sh
%{_datadir}/zsh/site-functions/_snap
%{_libexecdir}/snapd/snapd.run-from-snap
%{_sysconfdir}/profile.d/snapd.sh
%{_mandir}/man8/snapd-env-generator.8*
%{_systemd_system_env_generator_dir}/snapd-env-generator
%{_unitdir}/snapd.socket
%{_unitdir}/snapd.service
%{_unitdir}/snapd.seeded.service
%{_unitdir}/snapd.apparmor.service
%{_unitdir}/snapd.mounts.target
%{_unitdir}/snapd.mounts-pre.target
%{_userunitdir}/snapd.session-agent.service
%{_userunitdir}/snapd.session-agent.socket
%{_tmpfilesdir}/snapd.conf
%dir %{_prefix}/lib/dracut/dracut.conf.d
%{_prefix}/lib/dracut/dracut.conf.d/50-snapd.conf
%{_datadir}/dbus-1/services/io.snapcraft.Launcher.service
%{_datadir}/dbus-1/services/io.snapcraft.SessionAgent.service
%{_datadir}/dbus-1/services/io.snapcraft.Settings.service
%{_datadir}/dbus-1/session.d/snapd.session-services.conf
%{_datadir}/dbus-1/system.d/snapd.system-services.conf
%{_datadir}/polkit-1/actions/io.snapcraft.snapd.policy
%{_datadir}/applications/io.snapcraft.SessionAgent.desktop
%{_datadir}/fish/vendor_conf.d/snapd.fish
%{_datadir}/snapd/snapcraft-logo-bird.svg
%dir %{_prefix}/lib/dracut
%dir %{_prefix}/lib/dracut/dracut.conf.d
%{_prefix}/lib/dracut/dracut.conf.d/50-snapd.conf
%{_sysconfdir}/xdg/autostart/snap-userd-autostart.desktop
%config(noreplace) %{_sysconfdir}/sysconfig/snapd
%dir %{_localstatedir}/lib/snapd
%dir %{_localstatedir}/lib/snapd/assertions
%dir %{_localstatedir}/lib/snapd/cookie
%dir %{_localstatedir}/lib/snapd/cgroup
%dir %{_localstatedir}/lib/snapd/dbus-1
%dir %{_localstatedir}/lib/snapd/dbus-1/services
%dir %{_localstatedir}/lib/snapd/dbus-1/system-services
%dir %{_localstatedir}/lib/snapd/desktop
%dir %{_localstatedir}/lib/snapd/desktop/applications
%dir %{_localstatedir}/lib/snapd/device
%dir %{_localstatedir}/lib/snapd/environment
%dir %{_localstatedir}/lib/snapd/hostfs
%dir %{_localstatedir}/lib/snapd/inhibit
%dir %{_localstatedir}/lib/snapd/apparmor
%dir %{_localstatedir}/lib/snapd/apparmor/profiles
%dir %{_localstatedir}/lib/snapd/apparmor/snap-confine
%dir %{_localstatedir}/lib/snapd/cache
%dir %{_localstatedir}/lib/snapd/sequence
%dir %{_localstatedir}/lib/snapd/lib
%dir %{_localstatedir}/lib/snapd/lib/gl
%dir %{_localstatedir}/lib/snapd/lib/gl32
%dir %{_localstatedir}/lib/snapd/lib/glvnd
%dir %{_localstatedir}/lib/snapd/lib/vulkan
%dir %{_localstatedir}/lib/snapd/mount
%dir %{_localstatedir}/lib/snapd/seccomp
%dir %{_localstatedir}/lib/snapd/seccomp/bpf
%ghost %{_localstatedir}/lib/snapd/seccomp/bpf/global.bin
%dir %{_localstatedir}/lib/snapd/snaps
%dir %{_localstatedir}/lib/snapd/snap
%ghost %{_localstatedir}/lib/snapd/state.json
%ghost %{_localstatedir}/lib/snapd/system-key
%ghost %{_localstatedir}/lib/snapd/snap/bin
%ghost %{_localstatedir}/lib/snapd/snap/README
%dir %{_localstatedir}/cache/snapd
%ghost %{_localstatedir}/cache/snapd/commands
%ghost %{_localstatedir}/cache/snapd/names
%ghost %{_localstatedir}/cache/snapd/sections
%dir %{_localstatedir}/snap
%if %{with snap_symlink}
/snap
%endif
# this is typically owned by zsh, but we do not want to explicitly require zsh
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
# similar case for fish
%dir %{_datadir}/fish/vendor_conf.d

#%%dir %{_defaultdocdir}/snapd/
%{_defaultdocdir}/snapd/NEWS.md
#%%{_defaultdocdir}/snapd/README.md

%files -n snap-confine
%doc cmd/snap-confine/PORTING
%license COPYING
%dir %{_libexecdir}/snapd
%caps(%{snap_confine_caps}) %{_libexecdir}/snapd/snap-confine
%{_libexecdir}/snapd/snap-confine.caps
%{_libexecdir}/snapd/snap-confine.v2-only.caps
%{_libexecdir}/snapd/snap-device-helper
%{_libexecdir}/snapd/snap-discard-ns
%{_libexecdir}/snapd/snap-gdbserver-shim
%{_libexecdir}/snapd/snap-strace-shim
%{_libexecdir}/snapd/snap-seccomp
%{_libexecdir}/snapd/snap-update-ns
%{_mandir}/man8/snap-confine.8*
%{_mandir}/man8/snap-discard-ns.8*
%{_systemdgeneratordir}/snapd-generator
#%%attr(0111,root,root)  --prefix=/usr --sysconfdir=/etc --localstatedir=/var/lib/snapd/void

%if 0%{?with_selinux}
%files selinux
%license data/selinux/COPYING
%doc data/selinux/README.md
%{_datadir}/selinux/packages/snappy.pp.bz2
%{_datadir}/selinux/devel/include/contrib/snappy.if
%endif

%if 0%{?with_devel}
%files devel -f devel.file-list
%license COPYING
%doc README.md
%dir %{gopath}/src/%{provider}.%{provider_tld}/%{project}
%endif

%if 0%{?with_unit_test} && 0%{?with_devel}
%files unit-test-devel -f unit-test-devel.file-list
%license COPYING
%doc README.md
%endif

%post
# Create the private tmp directory for snap-confine
install -d -m 0700 /tmp/snap-private-tmp
%if 0%{?rhel} == 7
%sysctl_apply 99-snap.conf
%endif
# If install, test if snapd socket is enabled.
# If enabled, then attempt to start it. This will silently fail
# in chroots or other environments where services aren't expected
# to be started.
if [ $1 -eq 1 ] ; then
   if systemctl -q is-enabled snapd.socket > /dev/null 2>&1 ; then
      systemctl start snapd.socket > /dev/null 2>&1 || :
   fi
fi

%preun
# Remove all Snappy content if snapd is being fully uninstalled
if [ $1 -eq 0 ]; then
   %{_libexecdir}/snapd/snap-mgmt --purge || :
fi

%if 0%{?with_selinux}
%triggerun -- snapd < 2.39
# TODO: the trigger relies on a very specific snapd version that introduced SELinux
# mount context, figure out how to update the trigger condition to run when needed

# Trigger on uninstall, with one version of the package being pre 2.38 see
# https://rpm-packaging-guide.github.io/#triggers-and-scriptlets for details
# when triggers are run
if [ "$1" -eq 2 -a "$2" -eq 1 ]; then
   # Upgrade from pre 2.38 version
   %{_libexecdir}/snapd/snap-mgmt-selinux --patch-selinux-mount-context=system_u:object_r:snappy_snap_t:s0 || :

   # snapd might have created fontconfig cache directory earlier, but with
   # incorrect context due to bugs in the policy, make sure it gets the right one
   # on upgrade when the new policy was introduced
   if [ -d "%{_localstatedir}/cache/fontconfig" ]; then
      restorecon -R %{_localstatedir}/cache/fontconfig || :
   fi
elif [ "$1" -eq 1 -a "$2" -eq 2 ]; then
   # Downgrade to a pre 2.38 version
   %{_libexecdir}/snapd/snap-mgmt-selinux --remove-selinux-mount-context=system_u:object_r:snappy_snap_t:s0 || :
fi

%pre selinux
%selinux_relabel_pre

%post selinux
%selinux_modules_install %{_datadir}/selinux/packages/snappy.pp.bz2
%selinux_relabel_post

%posttrans selinux
%selinux_relabel_post

%postun selinux
%selinux_modules_uninstall snappy
if [ $1 -eq 0 ]; then
    %selinux_relabel_post
fi
%endif


