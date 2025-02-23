#!/bin/bash
VAEX_CACHE="memory,disk" VAEX_CACHE_DISK_SIZE_LIMIT="20GB" VAEX_CACHE_MEMORY_SIZE_LIMIT="4GB" uvicorn explorer_server.api:app
