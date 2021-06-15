FROM fedora:latest as base

RUN dnf install -y \
    which \
    make \
    automake \
    gcc \
    gcc-c++ \
    kernel-devel \
    python3-devel \
    poetry \
    java-1.8.0-openjdk.x86_64

WORKDIR /app

COPY . .

RUN poetry install

RUN echo "export JAVA_HOME=$(dirname $(dirname $(dirname $(readlink $(readlink $(which java))))))" >> ~/.bashrc

# RUN dnf remove -y \
#     which \
#     make \
#     automake \
#     gcc \
#     gcc-c++ \
#     kernel-devel \
#     python3-devel \
#     && dnf autoremove -y

# RUN rm -rf /var/cache/dnf \
#     && rm -rf /var/lib/rpm \
#     rm -rf /var/lib/dnf

CMD [ "poetry", "run", "dbload", "--help" ]
