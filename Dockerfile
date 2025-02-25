# start with python dependencies
FROM python:3.10-slim as dep-stage

# UV settings
# Enable bytecode compilation, copy from cache instal of links b/c mounted, dont download python
ENV UV_COMPILE_BYTECODE=1 
ENV UV_LINK_MODE=copy 
ENV UV_PYTHON_DOWNLOADS=0 

# setrup app dir
WORKDIR /tmp

# project files 
COPY ./pyproject.toml ./uv.lock ./

# install system requirements
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y postgresql-client git gh lmod procps cron rsync vim \
        build-essential \
        # these are for h5py in sdss_explorer
        curl libhdf5-dev pkg-config \
        # these are for vaex
        libpcre3 libpcre3-dev gcc g++ libboost-all-dev \
        libffi-dev python3-dev libxml2-dev libxslt-dev \
        libpq-dev zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Rust for sdss_explorer
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y && . /root/.cargo/env
ENV PATH="/root/.cargo/bin:$PATH"

# Add a command to check if cargo is available
RUN cargo --version

# setup correct wheels for vaex
# normal build hangs/fails like https://github.com/vaexio/vaex/issues/2382
# temp solution, see https://github.com/vaexio/vaex/pull/2331
#ENV PIP_FIND_LINKS=https://github.com/ddelange/vaex/releases/expanded_assets/core-v4.17.1.post4
#RUN pip install --force-reinstall vaex
#ENV PIP_FIND_LINKS=

# NOTE: unlike valis, don't need github creds for install of private sdss_explorer

# Installing uv and then project dependencies
RUN pip install uv
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev


# Stage 2: Development stage for the project
FROM dep-stage as dev-stage

# Copy the main project files over and install
COPY ./ ./

# install project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Create dir for socket and logs
# NOTE: i stole this from valis Dockerfile, don't know if necessary
RUN mkdir -p /tmp/webapp

# module setup
# this is overriden by wsgi cfg
ENV EXPLORER_SOCKET_DIR='/tmp/webapp' 
ENV SOLARA_CHECK_HOOKS="off"
ENV EXPLORER_NPROCESSES=4
ENV EXPLORER_NWORKERS=1
ENV VAEX_HOME="~/"
ENV VAEX_CACHE="memory,disk"
ENV VAEX_CACHE_DISK_SIZE_LIMIT="10GB"
ENV VAEX_CACHE_MEMORY_SIZE_LIMIT="1GB"

# label
LABEL org.opencontainers.image.source https://github.com/sdss/explorer
LABEL org.opencontainers.image.description "explorer production image"

# port goes out @ 8050
EXPOSE 8050

# NOTE: we set most envvars on startup
CMD ["uv", "run", "gunicorn", "-c", "src/sdss_explorer/server/wsgi_conf.py", "sdss_explorer.server.wsgi:app"]
