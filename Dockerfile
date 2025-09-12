FROM jenkins/jenkins:lts

USER root

# Instalar git, docker, docker-compose, curl, unzip, python3 y pip
RUN apt-get update && apt-get install -y \
    git \
    docker.io \
    docker-compose \
    curl \
    unzip \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Instalar AWS CLI v2
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf aws awscliv2.zip

# Instalar Node.js (ejemplo: versión LTS)
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs

USER jenkins
