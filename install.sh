#!/bin/bash

VENV=".vdenv"

[ -d $VENV ] && echo "$VENV already exists" || python3 -m venv $VENV

source $VENV/bin/activate

pip install -r requirements.txt


