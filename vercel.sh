#!/bin/bash

# Install Playwright browsers

# Install Python dependencies
pip install -r requirements.txt

playwright install

# Check if the environment is production or preview
if [[ $VERCEL_ENV == "production"  ]] ; then 
  npm run build:production
  playwright install
else 
  npm run build:preview
fi
