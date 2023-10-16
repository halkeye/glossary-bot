FROM python:3.10

ARG TINI_VERSION=v0.18.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/bin/tini
RUN chmod +x /usr/bin/tini

WORKDIR /app
COPY . /app
RUN pip --no-cache-dir install .

ENTRYPOINT [ "/usr/bin/tini", "--" ]
CMD ["python", "-u", "app.py"]
