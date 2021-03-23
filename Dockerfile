FROM python:3.8.8-slim-buster


ARG PROJECT_NAME=${PROJECT_NAME:-kps}
ARG HOST_UID=${HOST_UID:-9000}
ARG HOST_USER=${HOST_USER:-app}

ENV HOST_HOME=/home/$HOST_USER
ENV APP_DIR=$HOST_HOME/$PROJECT_NAME

# Create a new system user with proper permissions to its home directory
# so that all dependencies are installed properly
RUN adduser --home /home/$HOST_USER --uid $HOST_UID $HOST_USER --quiet --system \
        && chown -R $HOST_UID:$HOST_UID $HOST_HOME \
        && mkdir $APP_DIR

USER $HOST_USER
WORKDIR $APP_DIR
ENV PATH $HOST_HOME/.local/bin:$PATH

COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

# Updates contents and permission
COPY . .

EXPOSE 5000

CMD ["sh", "docker/entrypoint.sh"]
