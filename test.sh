#!/bin/sh

coverage run --source=./ tests.py;
coverage report -m;
rm -rf __pycache__/;
