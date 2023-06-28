#!/bin/sh

set -e
if df -h | grep -E "shm\s*(([0-9]{3,}M)|([0-9]+G))" > /dev/null; then
  sleep 0
else
  echo "This action required more than 64M of shm size, run this in your workflow before calling the action:"
  echo 'run: |'
  echo '  echo '{ "cgroup-parent": "/actions_job", "default-shm-size": "512M" }' | sudo tee /etc/docker/daemon.json && sudo systemctl reload docker'
  exit 1
fi

export STEAM_APP_ID=394360
export STEAM_LOGIN="$INPUT_STEAMLOGIN"
export STEAM_PASSWORD="$INPUT_STEAMPASSWORD"
export PDX_LOGIN="$INPUT_PDXLOGIN"
export PDX_PASSWORD="$INPUT_PDXPASSWORD"
export POP3_ADDRESS="$INPUT_POP3ADDRESS"
export POP3_USER="$INPUT_POP3USER"
export POP3_PASSWORD="$INPUT_POP3PASSWORD"
export POP3_PORT="$INPUT_POP3PORT"
if [ "$INPUT_POP3NOSSL" = "true" ]; then
  export POP3_NO_SSL="1"
else
  export POP3_NO_SSL="0"
fi
export DEBUG_IMAGES="$GITHUB_WORKSPACE/$INPUT_DEBUGIMAGEPATH"
export VNC_PASSWORD="$INPUT_DEBUGVNCPASSWORD"

cd $GITHUB_WORKSPACE

if [ -z "$INPUT_DESCRIPTIONPATH" ] || [ "$INPUT_DESCRIPTIONPATH" = "" ]; then
  sleep 0
else
  sudo cp "$INPUT_DESCRIPTIONPATH" "/home/steam/description.txt"
fi

if [ -z "$INPUT_DEBUGIMAGEPATH" ] || [ "$INPUT_DEBUGIMAGEPATH" = "" ]; then
  sleep 0
else
  sudo mkdir -p "$DEBUG_IMAGES"
fi
sudo rm -rf "$INPUT_MODPATH/.*"
sudo cp -R "$INPUT_MODPATH/." "/home/steam/.local/share/Paradox Interactive/Hearts of Iron IV/mod"
sudo chown -R steam:steam "/home/steam/.local/share/Paradox Interactive/Hearts of Iron IV/mod"
sudo chmod 777 -R "/home/steam/.local/share/Paradox Interactive/Hearts of Iron IV/mod"
ls "/home/steam/.local/share/Paradox Interactive/Hearts of Iron IV/mod"
sudo -Eu steam HOME=/home/steam /entrypoint.sh
