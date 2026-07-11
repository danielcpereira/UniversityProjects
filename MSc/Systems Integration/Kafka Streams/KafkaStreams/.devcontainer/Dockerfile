FROM maven:3.9.11-eclipse-temurin-24

# Adapted from:
# https://gist.github.com/MichalZalecki/4a87880bbe7a3a5428b5aebebaa5cd97
ARG USER_NAME="main"
ARG USER_PASSWORD="main"

# Install tools and create non-root user.
USER root

RUN set -eux \
  && apt-get update \
  && apt-get install -y --no-install-recommends curl \
  git \
  less \
  sudo \
  vim \
  wget \
  zsh \
  && rm -rf /var/lib/apt/lists/* \
  # Add a user (starts disabled until password is set).
  && adduser --disabled-password --gecos "User" --shell /bin/zsh --home /home/$USER_NAME ${USER_NAME} \
  # Update the password.
  && echo ${USER_NAME}:${USER_PASSWORD} | chpasswd \
  && groupadd -f wheel \
  && usermod -aG sudo,wheel ${USER_NAME} \
  && mkdir -p /workspace /home/${USER_NAME}/.m2 \
  && chown -R ${USER_NAME}:${USER_NAME} /workspace /home/${USER_NAME}

# install Kafka tooling
RUN curl -fSL -o kafka_2.13-4.2.0.tgz https://archive.apache.org/dist/kafka/4.2.0/kafka_2.13-4.2.0.tgz \
  && tar -xzf kafka_2.13-4.2.0.tgz \
  && rm -f kafka_2.13-4.2.0.tgz
ENV PATH="/kafka_2.13-4.2.0/bin/:${PATH}"

# Switch to the non-root user for shell customization.
USER $USER_NAME

# Ensure Maven uses a writable config path for non-root user.
ENV MAVEN_CONFIG=/home/${USER_NAME}/.m2

# Terminal colors with xterm.
ENV TERM xterm

# Set the zsh theme.
ENV ZSH_THEME robbyrussell

# Install Oh My Zsh non-interactively for devcontainer builds.
# RUN RUNZSH=no CHSH=no KEEP_ZSHRC=yes sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Start zsh.
CMD [ "zsh" ]