#!/bin/bash

tmux new-session -d -s lobe_server
tmux send-keys -t lobe_server ". /var/www/lobe.gto.is/venv/bin/activate" C-m
tmux send-keys -t lobe_server "cd /var/www/lobe.gto.is" C-m
tmux send-keys -t lobe_server "export export FLASK_INSTANCE_PATH=/var/www/lobe.gto.is/instance_folder_dev/" C-m
tmux send-keys -t lobe_server "/var/www/lobe.gto.is/venv/bin/mod_wsgi-express start-server /var/www/lobe.gto.is/wsgi.py --processes 2 --user www-data --group www-data --port 8932  --limit-request-body 52428800" C-m
