FROM python:3.10-slim-bullseye
EXPOSE 80

RUN apt update -y && apt install -y iproute2 && apt clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /home/user/application
COPY . /home/user/application

ENV PATH="/home/user/.local/bin:$PATH"
RUN pip install poetry
RUN poetry install

CMD ["/home/user/application/start.sh"]
