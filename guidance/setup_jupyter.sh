#!/bin/bash
#
# debug flags
#set -ex
source .venv/bin/activate

# Save old configuration file if exits
JUPYTER_CONFIG="$HOME/.jupyter/jupyter_lab_config.py"

mv ${JUPYTER_CONFIG} ${JUPYTER_CONFIG}_$(date +%F-%T)

echo 'y' | jupyter lab --generate-config 

read -s -p "Password: " PASSWORD 

echo ""
echo "entered passwrord ${PASSWORD}"
PASSWORD=$(python -c "from jupyter_server.auth import passwd; print(passwd('${PASSWORD}'))")

echo "before"
cat ${JUPYTER_CONFIG} | grep 'c.ServerApp.password'

sed -i "s|# c.ServerApp.password = ''|c.ServerApp.password  = '${PASSWORD}'|g"   ${JUPYTER_CONFIG} 

echo "after"
cat ${JUPYTER_CONFIG} | grep 'ServerApp.password'

sed -i "s/# c.ServerApp.allow_password_change = True/c.ServerApp.allow_password_change = True/g" ${JUPYTER_CONFIG}
sed -i "s/# c.ServerApp.ip = 'localhost'/c.ServerApp.ip='0.0.0.0'/g" 	    		        ${JUPYTER_CONFIG} 
sed -i "s/# c.ServerApp.port = 8888/c.ServerApp.port = 8888/g"		    		        ${JUPYTER_CONFIG} 
sed -i "s/# c.ServerApp.open_browser = True/c.ServerApp.open_browser = False/g"  	        ${JUPYTER_CONFIG} 

jupyter lab &
