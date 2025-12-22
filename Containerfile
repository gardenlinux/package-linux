FROM debian:testing

RUN apt-get update && apt-get -y install git python3 python3-dacite

WORKDIR /work

RUN git clone --depth=1 --branch=debian/6.12.57-1 https://salsa.debian.org/kernel-team/linux debian-linux

COPY buildcheck-print-configs.patch buildcheck-print-configs.patch
COPY config config
COPY entrypoint.sh /entrypoint.sh

WORKDIR /work/debian-linux
RUN ls debian/bin/buildcheck.py
RUN patch < ../buildcheck-print-configs.patch debian/bin/buildcheck.py

# ENTRYPOINT ["/entrypoint.sh"]

# CMD ["bash"]
