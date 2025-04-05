# BTS-OP-TEE

## Overview
BTS-OP-TEE is a project that provides a secure and efficient way to manage sensitive data using the OP-TEE (Open Portable Trusted Execution Environment) framework. It leverages the capabilities of OP-TEE to create a trusted environment for executing sensitive operations, ensuring data integrity and confidentiality for BTS voting mechanism

## requirements
- OP-TEE
- QEMU_v8
    - socat
- Ubuntu 22.04
- ngrok
- FastAPI

## Important Commands
### QEMU
mkdir /host
mount -t 9p -o trans=virtio hostshare /host
cd /host
socat TCP-LISTEN:6000,reuseaddr,fork EXEC:/bin/sh

### FastAPI
uvicorn main:app --host 0.0.0.0 --port 7999