#!/bin/sh

PROJECT=the_el
ROOT=/home/ubuntu/$PROJECT
SECRETS=/home/ubuntu/secrets.sh

export DJANGO_SETTINGS_MODULE=the_el.settings
. /home/ubuntu/.virtualenvs/$PROJECT/bin/activate

cd $ROOT
. $SECRETS
python /home/ubuntu/$PROJECT/manage.py load_positions
