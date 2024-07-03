#!/bin/bash
#
# debug flags
#set -ex
source .venv/bin/activate

# Save old configuration file if exits
JUPYTER_CONFIG_DIR="$HOME/.jupyter"
JUPYTER_CONFIG="${JUPYTER_CONFIG_DIR}/jupyter_lab_config.py"

mv ${JUPYTER_CONFIG} ${JUPYTER_CONFIG}_$(date +%F-%T)

echo 'y' | jupyter lab --generate-config

read -s -p "Password: " PASSWORD
echo ""

PASSWORD=$(python -c "from jupyter_server.auth import passwd; print(passwd('${PASSWORD}'))")

sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout ${JUPYTER_CONFIG_DIR}/jupyter-selfsigned.key \
     -out $JUPYTER_CONFIG_DIR/jupyter-selfsigned.crt \
     -subj "/C=US"

sudo chown $USER ${JUPYTER_CONFIG_DIR}/jupyter-selfsigned.key

sed -i "s|# c.ServerApp.password = ''|c.ServerApp.password  = '${PASSWORD}'|g"                                  ${JUPYTER_CONFIG}
sed -i "s/# c.ServerApp.allow_password_change = True/c.ServerApp.allow_password_change = True/g"                ${JUPYTER_CONFIG}
sed -i "s/# c.ServerApp.ip = 'localhost'/c.ServerApp.ip='0.0.0.0'/g"                                            ${JUPYTER_CONFIG}
sed -i "s/# c.ServerApp.port = 0/c.ServerApp.port = 8888/g"                                                     ${JUPYTER_CONFIG}
sed -i "s/# c.ServerApp.open_browser = True/c.ServerApp.open_browser = False/g"                                 ${JUPYTER_CONFIG}
sed -i "s|# c.ServerApp.certfile = ''|c.ServerApp.certfile = u'${JUPYTER_CONFIG_DIR}/jupyter-selfsigned.crt'|g" ${JUPYTER_CONFIG}
sed -i "s|# c.ServerApp.keyfile = ''|c.ServerApp.keyfile = u'${JUPYTER_CONFIG_DIR}/jupyter-selfsigned.key'|g"   ${JUPYTER_CONFIG}

jupyter lab &
