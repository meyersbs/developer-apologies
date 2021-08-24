#!/bin/sh

rm -rf test_data/;
coverage run --source=./ tests.py;
coverage report -m;
rm -rf __pycache__/;
