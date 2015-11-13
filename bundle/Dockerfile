FROM mobilecloudnetworking/mcn_so_base_ops

WORKDIR /app

COPY . /app

EXPOSE 8080

ENV PYTHONPATH=/app
CMD ["/env/bin/python", "./wsgi/application"]

