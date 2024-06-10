#!/bin/bash
#
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# debug flags
# set -ex
source .venv/bin/activate

echo 'y' | jupyter notebook --generate-config

PASSWORD=$(python -c "from jupyter_server.auth import passwd; print(passwd('test123'))")

sed -i "s|# c.NotebookApp.password = ''|c.NotebookApp.password = '${PASSWORD}'|g"   ~/.jupyter/jupyter_notebook_config.py
sed -i "s/# c.NotebookApp.ip = 'localhost'/c.NotebookApp.ip='0.0.0.0'/g"            ~/.jupyter/jupyter_notebook_config.py
sed -i "s/# c.NotebookApp.port = 8888/c.NotebookApp.port = 8888/g"                  ~/.jupyter/jupyter_notebook_config.py
sed -i "s/# c.NotebookApp.open_browser = True/c.NotebookApp.open_browser = False/g" ~/.jupyter/jupyter_notebook_config.py

jupyter lab &
