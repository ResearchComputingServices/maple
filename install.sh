#!/bin/bash

VENV=".venv"

[ -d $VENV ] && echo "$VENV already exists" || python3 -m venv $VENV

source $VENV/bin/activate

pip install --upgrade pip

pip install -r requirements.txt

pip install python-socketio python-socketio[client]

cd maple_structures

pip install -e .

cd ../maple_proc

pip install -e .
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.6.0/en_core_web_sm-3.6.0.tar.gz


cd ../maple_interface

pip install -e .

cd ../maple_config

pip install -e .

cd ../

cdir=$(pwd)
cd ~
[ -d rcs-utils ] && echo "rcs directory already exist" || git clone git@github.com:ResearchComputingServices/rcs-utils.git
cd rcs-utils
git pull
pip install -e .
cd $cdir


# pm2 start scripts/chatgpt_process.py --interpreter .venv/bin/python3 
# pm2 start maple_data_fetcher/data_fetcher.py --interpreter .venv/bin/python3  -- -e prod -i 600 -l info -o