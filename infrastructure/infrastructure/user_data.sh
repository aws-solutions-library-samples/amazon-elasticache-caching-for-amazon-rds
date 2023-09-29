#!/usr/bin/sh

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

export INSTALL_LOG="/home/ec2-user/install.log"
export EC2_PROFILE="/home/ec2-user/.bash_profile"

sudo yum update -y
sudo yum install -y \
    clang \
    git \
    gcc \
    jemalloc-devel \
    make \
	tcl \
	tcl-devel \
    tree \
    wget

sudo yum -y groupinstall "Development Tools"
sudo yum -y remove mysql-community-release

# OpenSSL
sudo yum remove -y openssl openssl-devel
# https://www.openssl.org/source/openssl-3.0.10.tar.gz
sudo yum install -y openssl11 openssl11-devel
openssl version >> ${INSTALL_LOG}

# Amazon Linux Extras
sudo amazon-linux-extras install -y epel

mkdir -p ~/tmp
cd ~/tmp

# Docker
sudo yum install -y docker
sudo usermod -a -G docker ec2-user
id ec2-user
newgrp docker
sudo systemctl enable docker.service
sudo systemctl start docker.service
sudo systemctl status docker.service

# Install Homebrew | https://brew.sh/
sudo -u ec2-user CI=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
(echo; echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"') >> ${EC2_PROFILE}

sudo chown -R ec2-user:ec2-user /home/ec2-user/*
