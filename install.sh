#!/usr/bin/env bash
set -e

APP_DIR="/opt/robot-app"
CONFIG_FILE="$APP_DIR/config.json"
SERVICE_NAME="robot-app"
PYTHON_BIN="/usr/bin/python3"
HOTSPOT_INTERFACE="wlan0"

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run with sudo"
  exit 1
fi

apt update
apt install -y git python3 python3-pip network-manager jq dnsmasq

if [[ ! -d "$APP_DIR" ]]; then
  git clone https://github.com/RoboticaWerenfridus/robot.app "$APP_DIR"
else
  git -C "$APP_DIR" pull
fi

if [[ -f "$APP_DIR/requirements.txt" ]]; then
  pip3 install -r "$APP_DIR/requirements.txt"
fi

read -rp "Do you have a standard robot? (Y/n): " STANDARD
STANDARD=${STANDARD:-Y}

if [[ "$STANDARD" =~ ^[Yy]$ ]]; then
  BACKWARDS=false
  L_FWD=6
  L_BWD=1
  R_FWD=12
  R_BWD=0
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
nmcli con add type wifi ifname $HOTSPOT_INTERFACE con-name "$ROBOT_NAME" autoconnect yes ssid "$ROBOT_NAME"
nmcli con modify "$ROBOT_NAME" 802-11-wireless.mode ap
nmcli con modify "$ROBOT_NAME" 802-11-wireless.band bg
nmcli con modify "$ROBOT_NAME" wifi-sec.key-mgmt wpa-psk
nmcli con modify "$ROBOT_NAME" wifi-sec.psk "$HOTSPOT_PASS"
nmcli con modify "$ROBOT_NAME" ipv4.method shared

cat >/etc/dnsmasq.d/robot-app.conf <<EOF
interface=$HOTSPOT_INTERFACE
dhcp-range=10.42.0.2,10.42.0.20,255.255.255.0,24h
address=/robot.app/10.42.0.1
EOF

systemctl restart dnsmasq

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

ROBOT_CMD_PATH="/usr/local/bin/robot-app"
cat >$ROBOT_CMD_PATH <<'EOF'
#!/usr/bin/env bash
set -e

SERVICE="robot-app"
HOTSPOT_NAME="$(nmcli -t -f NAME c | grep '^'${1:-})"
HOTSPOT_INTERFACE="wlan0"

if [[ $EUID -ne 0 ]]; then
  echo "Use sudo"
  exit 1
fi

if [[ "$1" == "on" ]]; then
  nmcli con up "$HOTSPOT_NAME"
  systemctl enable --now $SERVICE
  echo "Robot hotspot and service enabled"
elif [[ "$1" == "off" ]]; then
  nmcli con down "$HOTSPOT_NAME" || true
  systemctl disable --now $SERVICE
  echo "Robot hotspot and service disabled"
else
  echo "Usage: robot-app [on|off]"
fi
EOF

chmod +x $ROBOT_CMD_PATH

echo "Installation complete"
echo "Hotspot name: $ROBOT_NAME"
echo "Hotspot password: $HOTSPOT_PASS"
echo "Use 'sudo robot-app on' to start hotspot and service"
echo "Use 'sudo robot-app off' to stop hotspot and service"
