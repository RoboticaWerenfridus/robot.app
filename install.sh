#!/usr/bin/env bash
set -e

APP_DIR="/opt/robot-app"
CONFIG_FILE="$APP_DIR/config.json"
SERVICE_NAME="robot-app"
PYTHON_BIN="/usr/bin/python3"

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run with sudo"
  exit 1
fi

apt update
apt install -y git python3 python3-pip network-manager jq

if [[ ! -d "$APP_DIR" ]]; then
  git clone https://github.com/RoboticaWerenfridus/robot.app "$APP_DIR"
else
  git -C "$APP_DIR" pull
fi

if [[ -f "$APP_DIR/requirements.txt" ]]; then
  pip3 install -r "$APP_DIR/requirements.txt"
fi

echo "ROBOT SETUP WIZARD"

read -rp "Do you have a standard robot? (Y/n): " STANDARD
STANDARD=${STANDARD:-Y}

if [[ "$STANDARD" =~ ^[Yy]$ ]]; then
  BACKWARDS=false
  L_FWD=6
  L_BWD=6
  R_FWD=12
  R_BWD=12
else
  BACKWARDS=true
  L_FWD=17
  L_BWD=18
  R_FWD=22
  R_BWD=23
fi

read -rp "What is the name of your robot? " ROBOT_NAME
if [[ -z "$ROBOT_NAME" ]]; then
  echo "Robot name cannot be empty"
  exit 1
fi

read -rp "What password do you want for your hotspot? (empty = 12345678): " HOTSPOT_PASS
HOTSPOT_PASS=${HOTSPOT_PASS:-12345678}

if [[ ${#HOTSPOT_PASS} -lt 8 ]]; then
  echo "Password must be at least 8 characters"
  exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
  jq -n '{}' > "$CONFIG_FILE"
fi

jq \
  --argjson backwards "$BACKWARDS" \
  --argjson lf "$L_FWD" \
  --argjson lb "$L_BWD" \
  --argjson rf "$R_FWD" \
  --argjson rb "$R_BWD" \
  '
  .backwards_enabled = $backwards |
  .motors.left.forward = $lf |
  .motors.left.backward = $lb |
  .motors.right.forward = $rf |
  .motors.right.backward = $rb
  ' "$CONFIG_FILE" > /tmp/config.json

mv /tmp/config.json "$CONFIG_FILE"

nmcli con delete "$ROBOT_NAME" 2>/dev/null || true
nmcli con add type wifi ifname wlan0 con-name "$ROBOT_NAME" autoconnect yes ssid "$ROBOT_NAME"
nmcli con modify "$ROBOT_NAME" 802-11-wireless.mode ap
nmcli con modify "$ROBOT_NAME" 802-11-wireless.band bg
nmcli con modify "$ROBOT_NAME" wifi-sec.key-mgmt wpa-psk
nmcli con modify "$ROBOT_NAME" wifi-sec.psk "$HOTSPOT_PASS"
nmcli con modify "$ROBOT_NAME" ipv4.method shared
nmcli con up "$ROBOT_NAME"

cat >/etc/systemd/system/$SERVICE_NAME.service <<EOF
[Unit]
Description=Robot App
After=network.target

[Service]
ExecStart=$PYTHON_BIN $APP_DIR/app.py
WorkingDirectory=$APP_DIR
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reexec
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl restart $SERVICE_NAME

echo "Installation complete"
echo "Hotspot name: $ROBOT_NAME"
echo "Hotspot password: $HOTSPOT_PASS"
