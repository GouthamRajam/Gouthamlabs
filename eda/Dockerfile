# s2s-eda — reproducible open-source EDA environment (milestone M0.1).
# Pinned versions live in eda/versions.lock (the FROM digest below must match its base_image).
#
# Base: the official OpenLane 2.3.10 image, pinned by digest. It already ships
# OpenLane 2, Yosys, OpenROAD, OpenSTA, Verilator, Icarus Verilog, SymbiYosys, eqy,
# Magic, KLayout and Netgen as one tested toolchain. This file adds what it lacks:
# the SKY130 PDK (sky130A, with sky130_fd_sc_hd plus the other libraries OpenLane's
# sky130 config requires), cocotb, and the support tools needed to actually run
# simulation and formal (make, clang, perl, awk, sed, yices, z3; added in M0.2).
#
# Build (from the repo root):  docker build -t s2s-eda eda/
# Behind a TLS-intercepting proxy, pass its CA as an optional build secret:
#   docker build --secret id=proxy_ca,src=/path/to/ca.crt -t s2s-eda eda/
FROM ghcr.io/efabless/openlane2:2.3.10@sha256:37c3bd4ea0534a276cb2deb88d601044857bad2807b9bc5b36efe9d02c62624e

ENV PDK_ROOT=/opt/pdk \
    PDK=sky130A \
    STD_CELL_LIBRARY=sky130_fd_sc_hd

# versions.lock is the single source of truth for the pins below.
COPY versions.lock /opt/s2s/eda/versions.lock

# SKY130 PDK. Every archive listed in versions.lock (sky130_pdk_sha256_*) is fetched
# by direct release URL and checked against its pinned sha256, then unpacked into
# volare's version store; `volare enable` then finds it locally (no GitHub API call)
# and activates sky130A/sky130B.
RUN --mount=type=secret,id=proxy_ca,required=false \
    bash -euo pipefail -c ' \
    if [ -s /run/secrets/proxy_ca ]; then export SSL_CERT_FILE=/run/secrets/proxy_ca NIX_SSL_CERT_FILE=/run/secrets/proxy_ca; fi; \
    lock=/opt/s2s/eda/versions.lock; \
    rev=$(grep "^sky130_pdk=" $lock | cut -d= -f2); \
    url=https://github.com/chipfoundry/volare/releases/download/sky130-$rev; \
    mkdir -p /tmp/pdkdl && cd /tmp/pdkdl; \
    libs=(); \
    for line in $(grep "^sky130_pdk_sha256_" $lock); do \
      name=${line#sky130_pdk_sha256_}; name=${name%%=*}; sum=${line#*=}; \
      curl -fsSL --retry 4 -o "$name.tar.zst" "$url/$name.tar.zst"; \
      echo "$sum  $name.tar.zst" | sha256sum -c -; \
      [ "$name" = common ] || libs+=(-l "$name"); \
    done; \
    python3 -c "import sys,tarfile,zstandard; [tarfile.open(fileobj=zstandard.open(f, \"rb\"), mode=\"r|\").extractall(sys.argv[1]) for f in sys.argv[2:]]" \
        "$PDK_ROOT/volare/sky130/versions/$rev" *.tar.zst; \
    volare enable --pdk sky130 --pdk-root "$PDK_ROOT" "${libs[@]}" "$rev"; \
    test -d "$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/lib"; \
    cd / && rm -rf /tmp/pdkdl'

# cocotb in its own venv (the base Python has no pip). Its bin dir is appended to
# PATH so `python3` stays the base interpreter that OpenLane needs.
RUN --mount=type=secret,id=proxy_ca,required=false \
    bash -euo pipefail -c ' \
    if [ -s /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    ver=$(grep "^cocotb=" /opt/s2s/eda/versions.lock | cut -d= -f2); \
    python3 -m venv /opt/cocotb; \
    /opt/cocotb/bin/pip install --no-cache-dir --disable-pip-version-check "cocotb==$ver"; \
    /opt/cocotb/bin/cocotb-config --version'
ENV PATH="${PATH}:/opt/cocotb/bin"

# Support tools the base image lacks (make, clang, perl, awk, sed, yices, z3, click): every
# versions.lock `nix_store_path_*` entry is installed into the /nix/var/nix/profiles/s2s
# profile. They are prebuilt binaries from cache.nixos.org, checked against the signing key
# the base image already trusts, and the store hash pins their exact content.
# yosys-witness (used by SymbiYosys to write counterexample traces) is shipped without its
# `click` dependency; a wrapper in /opt/s2s/bin adds it.
RUN --mount=type=secret,id=proxy_ca,required=false \
    bash -euo pipefail -c ' \
    if [ -s /run/secrets/proxy_ca ]; then export NIX_SSL_CERT_FILE=/run/secrets/proxy_ca; fi; \
    paths=$(grep "^nix_store_path_" /opt/s2s/eda/versions.lock | cut -d= -f2); \
    nix-env -p /nix/var/nix/profiles/s2s -i $paths; \
    witness=$(command -v yosys-witness); \
    mkdir -p /opt/s2s/bin; \
    printf "#!%s\nexport PYTHONPATH=/nix/var/nix/profiles/s2s/lib/python3.11/site-packages\${PYTHONPATH:+:\$PYTHONPATH}\nexec %s \"\$@\"\n" \
        "$(command -v bash)" "$witness" > /opt/s2s/bin/yosys-witness; \
    chmod +x /opt/s2s/bin/yosys-witness'
ENV PATH="/opt/s2s/bin:${PATH}:/nix/var/nix/profiles/s2s/bin"

COPY scripts/ /opt/s2s/eda/scripts/

WORKDIR /work
CMD ["bash"]
