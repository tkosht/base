#!/usr/bin/sh
set -eu

d=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
cd "$d/../"

curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | sudo gpg --batch --yes --dearmor -o /usr/share/keyrings/cloud.google.gpg

printf "%s\n" "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
  | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list

sudo apt-get update
sudo apt-get install -y google-cloud-cli

gcloud version
