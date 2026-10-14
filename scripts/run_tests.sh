#!/bin/sh
cd /Users/vanukuridhathri/Desktop/smart-agriculture-mlops
python -m pytest tests/ -q --no-header -p no:cacheprovider --tb=short > /tmp/pytest_full.txt 2>&1
echo "EXIT=$?" >> /tmp/pytest_full.txt
