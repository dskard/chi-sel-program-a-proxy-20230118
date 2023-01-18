# syntax=docker/dockerfile:1.4
FROM ubuntu:focal-20200423

ARG R_VERSION=4.2.0
ARG R_PACKAGES="c('shiny', 'rmarkdown', 'reticulate')"
ARG R_PACKAGES_REPO="https://packagemanager.rstudio.com/cran/__linux__/focal/latest"
ARG PYTHON_VERSION=3.10.0
ARG SSOS_VERSION=1.5.20.1002

# Don't print "debconf: unable to initialize frontend: Dialog" messages
ENV DEBIAN_FRONTEND=noninteractive

# =====================================================================
# install dev tools
# =====================================================================

# Install tools for development and debugging
RUN apt-get update && apt-get install -y \
        curl \
        gdebi-core \
        less \
        openssl \
        sudo \
        vim-tiny \
        wget \
        && \
    rm -rf /var/lib/apt/lists/*

# =====================================================================
# setup user accounts
# =====================================================================

# Create docker user with empty password (will have uid and gid 1000)
RUN useradd --create-home --shell /bin/bash docker \
    && passwd docker -d \
    && adduser docker sudo

# Don't require a password for sudo
RUN sed -i 's/^\(%sudo.*\)ALL$/\1NOPASSWD:ALL/' /etc/sudoers

# =====================================================================
# setup ssh login
# =====================================================================

RUN apt-get -qqy update && apt-get install -y \
        openssh-server \
        && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /var/run/sshd

# update user passwords
RUN echo 'root:root' | chpasswd
RUN echo 'docker:docker' | chpasswd

# open the container's port 22
EXPOSE 22

# start the sshd daemon
CMD ["/usr/sbin/sshd", "-D"]

# =====================================================================
# install R and R packages
# =====================================================================

RUN apt-get update && apt-get install -y \
        fonts-texgyre \
        && \
    rm -rf /var/lib/apt/lists/*

## Install a version of R
RUN set -e; \
    apt-get update; \
    curl -O https://cdn.rstudio.com/r/ubuntu-2004/pkgs/r-${R_VERSION}_1_amd64.deb; \
    gdebi -n r-${R_VERSION}_1_amd64.deb; \
    update-alternatives --install /usr/bin/R R /opt/R/${R_VERSION}/bin/R 1; \
    rm r-${R_VERSION}_1_amd64.deb; \
    rm -rf /var/lib/apt/lists/*;

# create a Rprofile.site with settings for downloading binary packages from RSPM
# https://docs.rstudio.com/rspm/admin/serving-binaries/#binary-user-agents
COPY <<-EOF /opt/R/${R_VERSION}/lib/R/etc/Rprofile.site
    options(
        repos = c(CRAN = "${R_PACKAGES_REPO}"),
        download.file.method = "libcurl",
        # Detect number of physical cores
        Ncpus = parallel::detectCores(logical=FALSE),
        HTTPUserAgent = sprintf("R/%s R (%s)", getRversion(), paste(getRversion(), R.version["platform"], R.version["arch"], R.version["os"]))
    )
EOF

## Install R packages
RUN /opt/R/${R_VERSION}/bin/R -e "install.packages(${R_PACKAGES}, repos='${R_PACKAGES_REPO}')";

# =====================================================================
# install Python
# =====================================================================

RUN set -e; \
    apt-get update; \
    curl -O https://cdn.rstudio.com/python/ubuntu-2004/pkgs/python-${PYTHON_VERSION}_1_amd64.deb; \
    sudo gdebi -n python-${PYTHON_VERSION}_1_amd64.deb; \
    update-alternatives --install /usr/bin/python3.10 python3.10 /opt/python/${PYTHON_VERSION}/bin/python3 1; \
    update-alternatives --install /usr/bin/pip3.10 pip3.10 /opt/python/${PYTHON_VERSION}/bin/pip3 1; \
    rm python-${PYTHON_VERSION}_1_amd64.deb; \
    rm -rf /var/lib/apt/lists/*;

# =====================================================================
# install Shiny Server
# =====================================================================

# install shiny server
RUN set -ex; \
    apt-get update; \
    wget https://download3.rstudio.org/ubuntu-18.04/x86_64/shiny-server-${SSOS_VERSION}-amd64.deb; \
    gdebi -n shiny-server-${SSOS_VERSION}-amd64.deb; \
    rm -f shiny-server-${SSOS_VERSION}-amd64.deb; \
    rm -rf /var/lib/apt/lists/*;

COPY shiny-server.sh /opt/shiny-server/bin/shiny-server.sh

RUN chmod 744 /opt/shiny-server/bin/shiny-server.sh
