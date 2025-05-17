# kt-scraper (KillTony Scraper)

This is a scraper for the KillTony/comedymothership website. It scrapes the /shows page and is able to generate a json file
as well as use a Discord webhook to send the alert to your phone.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Installation

Instructions on how to install and set up the project.

```bash
# Example command
git clone https://github.com/ThePotato456/kt-scraper.git
cd kt-scraper
pip install -r requirements.txt
```

## Usage

You can run the project in two ways: directly or through the script

```bash
python track_shows.py
```
or like this to have it save log output to log.txt
```bash
./run.sh
```
If you want to have the script run at midnight every night, you can use this crontab configuration.
Open crontab configuration and add this configuration to the bottom; make sure to grab both lines
```bash
crontab -e

TZ=America/Chicago
0 0 * * * cd /home/user/vscode_projects/kt-scraper/ && ./.venv/bin/python track_shows.py >> log.txt 2>&1
```


## License

This project is not under any license; This project is proprietary.