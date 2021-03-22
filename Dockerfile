FROM python:3.8.8-slim-buster

# python is already updated
# os is already updated

WORKDIR /app
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

COPY . . 
EXPOSE 5000

ENV HOST_UID $(id -u)
ENV HOST_USER  

RUN [ $USER == "root" ] || \
    (adduser -h /home/$(whoami) -D -u $(whoami) 
# CMD uvicorn src.server.app:app --port 5000 --host 0.0.0.0 --loop uvloop --log-level info --workers 8
CMD ["sh", "docker/entrypoint.sh"]


