#!/bin/bash

VENV=".venv"
usage(){
    echo "install maple project."
    echo ""
    echo "Syntax:"
    echo "./install.sh [-hpg] "
    echo
    echo "options"
    echo "h     help"
    echo "p     create pm2 tasks"
    echo "g     install required python packages."
    echo 
}


install_packages(){
    [ -d $VENV ] && echo "$VENV already exists" || python3 -m venv $VENV

    source $VENV/bin/activate

    pip install --upgrade pip

    pip install -r requirements.txt

    pip install --upgrade pip setuptools

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

    cd ../maple_chat

    pip install -e .

    cd ../

    cdir=$(pwd)
    cd ~
    [ -d rcs-utils ] && echo "rcs directory already exist" || git clone git@github.com:ResearchComputingServices/rcs-utils.git
    cd rcs-utils
    git pull
    pip install -e .

    cd ../
    [ -d RTPTResearch ] && echo "RTPTResearch directory already exist" || git clone git@github.com:ResearchComputingServices/RTPTResearch.git
    cd RTPTResearch
    git pull
    pip install -e .
    
    
    cd $cdir
}

create_pm2_tasks(){
    pm2 delete chatgpt 2> /dev/null && pm2 start runtime_scripts/chatgpt.py --interpreter .venv/bin/python3 
    pm2 delete data_fetcher 2> /dev/null && pm2 start maple_data_fetcher/data_fetcher.py --interpreter .venv/bin/python3  -- -e prod -i 600 -l info
    pm2 delete delete_model_iteration 2> /dev/null && pm2 start runtime_scripts/delete_model_iteration.py --interpreter .venv/bin/python3 -- -t old -a -c -l debug --use_config
    pm2 delete maple_models_bert 2> /dev/null && pm2 start runtime_scripts/maple_models.py --interpreter .venv/bin/python3 --name maple_models_bert -- --model bert --level debug --logname maple_models_bert
    pm2 save
    pm2 kill
    pm2 resurrect
    pm2 startup
    sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u $USER --hp $HOME
}

while getopts "hpg" arg; do
    case "${arg}" in 
        p)
            create_pm2_tasks
            ;;
        g) 
            install_packages
            ;;
        h) 
            usage
            exit
            ;;
    esac
done
