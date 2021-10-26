#!/bin/sh

rm -rf test_data/;
rm -rf test_data_2/;
coverage run --source=./ tests.py;
coverage report -m;
rm -rf __pycache__/;
