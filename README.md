```markdown
# RFID Project Setup Guide

This guide outlines the steps to set up the environment for the RFID project on a Raspberry Pi running the Bullseye OS.

## Table of Contents

- [Environment Setup](#environment-setup)
- [Webserver Setup](#webserver-setup)
- [API Server Setup](#api-server-setup)
- [OS Setup](#os-setup)
- [Additional Configuration](#additional-configuration)

CCFFFF20051000-3400E2004709B4706821BE0D010C-B75F

## Environment Setup

Before you begin, update your package list and upgrade your system:

```bash
sudo apt update
sudo apt upgrade
```

Install the necessary packages for your terminal and development environment:

```bash
sudo apt update
sudo apt install nala

echo "deb [signed-by=/usr/share/keyrings/azlux-archive-keyring.gpg] http://packages.azlux.fr/debian/ bookworm main" | sudo tee /etc/apt/sources.list.d/azlux.list
sudo wget -O /usr/share/keyrings/azlux-archive-keyring.gpg  https://azlux.fr/repo.gpg
sudo nala update

sudo nala install zsh exa fzf ripgrep neovim tmux git neofetch zsh-syntax-highlighting nginx nodejs npm postgresql postgresql-contrib tmux zsh-autosuggestions thefuck lm-sensors log2ram

curl -LO https://github.com/ClementTsang/bottom/releases/download/0.9.6/bottom_0.9.6_arm64.deb
sudo dpkg -i bottom_0.9.6_arm64.deb
```

Change your default shell to Zsh:

```bash
chsh -s $(which zsh)
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
sh -c "$(wget https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh -O -)"
```


https://gist.github.com/dogrocker/1efb8fd9427779c827058f873b94df95

then

https://dev.to/andrenbrandao/terminal-setup-with-zsh-tmux-dracula-theme-48lm

then

(git colorize tmux colored-man-pages zsh-autosuggestions zsh-syntax-highlighting thefuck 

and

https://medium.com/today-i-learned-chai/setup-node-js-application-with-pm2-and-nginx-72840f44ea73

and

https://vexell.medium.com/pm2-module-to-monitoring-node-js-application-with-export-to-prometheus-and-grafana-43d4b958c563
```

Tmux:
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm

Install Nerd Fonts for additional glyphs:

```bash
# Replace <nerd-fonts-download-url> and <nerd-fonts-zip-file> with actual values
wget <nerd-fonts-download-url>
unzip <nerd-fonts-zip-file>
cp <nerd-fonts-files> /usr/share/fonts/
cp <nerd-fonts-files> /usr/local/share/fonts/
fc-cache -f -v
```
sudo npm install -g pm2
sudo npm install gg
npm install body-parser

apt install postgres postgres-contrib


Set up Message of the Day (MOTD) using ASCII art:

```bash
# Generate ASCII art at the provided TAAG link and add it to your MOTD file
```

Configure SSH with no root passwords and a custom port:

```bash
# Edit your sshd_config file to include:
PermitRootLogin no
Port 8997
```

Install additional utilities:

## Webserver Setup

Install and configure Nginx:

```bash
sudo apt install nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

## API Server Setup

Install Node.js and npm, and the necessary Node packages:
https://medium.com/today-i-learned-chai/setup-node-js-application-with-pm2-and-nginx-72840f44ea73

```bash
sudo apt install nodejs npm
npm install ntp express ntp-client express ejs axios ntp-time pm2
sudo env PATH=$PATH:/usr/bin /usr/local/lib/node_modules/pm2/bin/pm2 startup systemd -u pi --hp /home/pi
```

This README is part of the RFID project documentation. For more information, visit the [project repository](#).
