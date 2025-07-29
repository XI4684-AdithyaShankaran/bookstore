FROM python:3.10.14-alpine AS base
ENV VENV_PATH="/opt/venv" PATH="${VENV_PATH}/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN apk update && apk add --no-cache python3 py3-pip py3-virtualenv build-base libffi-dev openssl-dev sqlite-dev gcc musl-dev python3-dev postgresql-dev
RUN python3 -m venv $VENV_PATH && $VENV_PATH/bin/pip install --no-cache-dir --upgrade pip setuptools wheel
COPY requirements.txt /tmp/requirements.txt
RUN $VENV_PATH/bin/pip install --no-cache-dir -r /tmp/requirements.txt