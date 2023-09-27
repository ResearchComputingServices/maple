#!/bin/bash

VENV=".venv"

[ -d $VENV ] && echo "$VENV already exists" || python3 -m venv $VENV

source $VENV/bin/activate

pip install --upgrade pip

pip install -r requirements.txt

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


