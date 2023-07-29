#!/bin/bash

VENV=".venv"

[ -d $VENV ] && echo "$VENV already exists" || python3 -m venv $VENV

source $VENV/bin/activate

pip install -r requirements.txt

cd maple-structures

pip install -e .

cd ../
