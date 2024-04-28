#!/bin/bash
# Builds the Docker image for the AWS Lambda deployment.
# Usage:
#   ./docker/build.sh

set -e

WIKIBOT_ECR_URI=725596835855.dkr.ecr.us-east-1.amazonaws.com/wiki-bot

# Checks that the home directory is the root of the project.
if [[ ! -f "wikibot/__init__.py" ]]; then
  echo "Error: Please run this script from the root of the project."
  exit 1
fi

# Builds the API Docker image.
docker build -t wiki-bot -f docker/Dockerfile .

# Log in to ECR.
aws ecr get-login-password | docker login --username AWS --password-stdin ${WIKIBOT_ECR_URI}

# Pushes the Docker image to ECR.
docker tag wiki-bot:latest ${WIKIBOT_ECR_URI}:latest
docker push ${WIKIBOT_ECR_URI}:latest

# Runs the Docker image locally.
# docker run wiki-bot:latest
