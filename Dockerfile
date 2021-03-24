FROM python:3.8.8-slim-buster


ARG PROJECT_NAME=${PROJECT_NAME:-kps}
ARG HOST_UID=${HOST_UID:-9000}
ARG HOST_USER=${HOST_USER:-app}

ENV HOST_HOME=/home/$HOST_USER
ENV APP_DIR=$HOST_HOME/$PROJECT_NAME
ENV PATH $HOST_HOME/.local/bin:$PATH

# Create a user specifically for app running
# Sets them with enough permissions in its home dir
RUN adduser --home $HOST_HOME --uid $HOST_UID $HOST_USER --quiet --system --group \
        && chown -R $HOST_UID:$HOST_UID $HOST_HOME/ \
        && chmod -R 770 $HOST_HOME \
        && chmod g+s $HOST_HOME 

# Switches to created user
USER $HOST_UID

# Creates an app dir
RUN mkdir $APP_DIR
WORKDIR $APP_DIR

# Copies and installs requirements
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

# Finishes copying code
COPY . .

EXPOSE 5000

CMD ["sh", "docker/entrypoint.sh"]
