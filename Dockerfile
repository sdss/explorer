# this Dockerfile sets up and runs the explorer download server, for handling the
# downloading of data subsets from the dashboard UI.

# start with python dependencies
FROM python:3.10-slim AS dep-stage

# UV settings
# Enable bytecode compilation, copy from cache instal of links b/c mounted, dont download python
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0
ENV VIRTUAL_ENV=/app/venv

# setrup app dir
WORKDIR /app

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

# Installing uv and then project dependencies
RUN pip install uv
RUN uv venv /app/venv # make venv
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev


# Stage 2: Development stage for the project
FROM dep-stage AS dev-stage

# Copy the main project files over and install
COPY ./ ./

# install project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# production build
FROM dev-stage AS build-stage

# place executables in the environment at the front of the path
ENV PATH="/app/venv/bin:$PATH"

# Create dir for socket and logs
# NOTE: i stole this from valis Dockerfile, don't know if necessary
RUN mkdir -p /app/webapp

# module setup
# this is overriden by wsgi cfg
ENV EXPLORER_SOCKET_DIR='/app/webapp'
ENV SOLARA_CHECK_HOOKS="off"
ENV SOLARA_THEME_SHOW_BANNER="False"
ENV EXPLORER_NPROCESSES=4
ENV EXPLORER_NWORKERS=1
ENV VAEX_HOME="~/"
ENV VAEX_CACHE="memory,disk"
ENV VAEX_CACHE_DISK_SIZE_LIMIT="10GB"
ENV VAEX_CACHE_MEMORY_SIZE_LIMIT="1GB"
ENV GUNICORN_CMD_ARGS="--reload --preload --workers=${EXPLORER_NWORKERS} -c src/sdss_explorer/server/wsgi_conf.py"

# label
LABEL org.opencontainers.image.source=https://github.com/sdss/explorer
LABEL org.opencontainers.image.description="explorer production image"

# port goes out @ 8050
EXPOSE 8050

# NOTE: we set most envvars on startup
CMD ["uv", "run", "gunicorn", "sdss_explorer.server.wsgi:app"]
