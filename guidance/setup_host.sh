#!/bin/bash
#
sudo yum install gcc python3-devel -y
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
