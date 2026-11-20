#!/bin/bash
# Установка робота на сервер (Ubuntu/Debian). Запуск: bash setup.sh
set -e
sudo apt-get update -qq && sudo apt-get install -y -qq python3-pip python3-venv >/dev/null
mkdir -p ~/robot && cd ~/robot
for f in robot.py login.py; do curl -fsSL "https://raw.githubusercontent.com/roza54468542-lgtm/limity/main/robot/$f" -o $f; done
python3 -m venv venv && ./venv/bin/pip install -q telethon
echo
echo "WORKER_URL=https://limity-okx.roza54468542.workers.dev" >> .env
read -p 'Ключ приложения (из Лимиты → ⚙ → OKX): ' K; echo "APP_KEY=$K" >> .env
read -p 'Название группы [Заявки UAH/PLN]: ' C; echo "CHAT=${C:-Заявки UAH/PLN}" >> .env
./venv/bin/python login.py
sudo tee /etc/systemd/system/robot.service >/dev/null <<UNIT
[Unit]
Description=Robot zayavki
After=network-online.target
[Service]
WorkingDirectory=$HOME/robot
ExecStart=$HOME/robot/venv/bin/python robot.py
Restart=always
RestartSec=5
User=$USER
[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload && sudo systemctl enable --now robot
sleep 5 && sudo journalctl -u robot -n 5 --no-pager
echo; echo 'Робот запущен. Он сам перезапускается после сбоев и перезагрузки сервера.'
