#!/usr/bin/sh

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

export INSTALL_LOG="/home/ec2-user/install.log"
export EC2_PROFILE="/home/ec2-user/.bash_profile"

source ${EC2_PROFILE}

docker version >> ${INSTALL_LOG}


# Install Homebrew | https://brew.sh/ | ===========================================================
# CI=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# (echo; echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"') >> ${EC2_PROFILE}
# eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
brew --version >> ${INSTALL_LOG}
brew update 
brew upgrade


# Install NodeJS | https://github.com/nvm-sh/nvm | ================================================
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
source ${EC2_PROFILE}
nvm --version >> ${INSTALL_LOG}

# nvm install 14
# brew install node@14
# node -v >> ${INSTALL_LOG}
# npm -v >> ${INSTALL_LOG}

# nvm install 16
# brew install node@16
# node -v >> ${INSTALL_LOG}
# npm -v >> ${INSTALL_LOG}

brew install node
npm install -g npm@10.1.0
npm -v >> ${INSTALL_LOG}


# Install Python | https://github.com/pyenv/pyenv | ===============================================
# brew install pipenv
# brew install pyenv
# echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ${EC2_PROFILE}
# echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ${EC2_PROFILE}
# echo 'eval "$(pyenv init -)"' >> ${EC2_PROFILE}
# source ${EC2_PROFILE}
# pyenv --version >> ${INSTALL_LOG}
brew install python@3.10
python3.10 -V >> ${INSTALL_LOG}

brew install python@3.11
python3.11 -V >> ${INSTALL_LOG}
python3 -V >> ${INSTALL_LOG}


# Databases | =====================================================================================


# Redis | -----------------------------------------------------------------------------------------
brew install redis
redis-benchmark --version >> ${INSTALL_LOG}
redis-cli --version >> ${INSTALL_LOG}
redis-server --version >> ${INSTALL_LOG}


# MariaDB Server | https://github.com/MariaDB/server | --------------------------------------------
# brew install mariadb@11.0
# brew install mariadb


# MySQL Server | https://github.com/mysql/mysql-server | ------------------------------------------
# brew install mysql@8.0
brew install mysql
mysql --version >> ${INSTALL_LOG}
# MySQL CLI | https://github.com/dbcli/mycli
brew install mycli
mycli -V >> ${INSTALL_LOG}


# PostgreSQL Server | https://www.postgresql.org/ | -----------------------------------------------
brew install postgresql@15
# PostgreSQL CLI | https://github.com/dbcli/pgcli
brew install pgcli

# List installed services
brew services list >> ${INSTALL_LOG}


# Other tools | ===================================================================================

# AWS | -------------------------------------------------------------------------------------------
brew install awscli
# Install CDK
npm install -g aws-cdk

# Linux | -----------------------------------------------------------------------------------------
brew install btop
brew install htop
brew install jq
brew install neofetch
brew install yq

# K8S | -------------------------------------------------------------------------------------------
brew install cdk8s
brew install eksctl
brew install helm
brew install kubectl

# Test | ------------------------------------------------------------------------------------------
brew install httpie
brew install hey
brew install wrk

# Charm | -----------------------------------------------------------------------------------------
brew install gum
brew install rich
brew install vhs


chown -R ec2-user:ec2-user /home/ec2-user/*

# Better Together | ===============================================================================
# Download and configure the Amazon RDS + Amazon ElastiCache Harness Test
mkdir -p ~/aws
