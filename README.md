[![Pylint](https://github.com/mstuebner/EvernoteSync/actions/workflows/pylint.yml/badge.svg?branch=master)](https://github.com/mstuebner/EvernoteSync/actions/workflows/pylint.yml)

# Scripts to sync data and files to Evernote

The script **directory_monitor.py** reads configuration from configs/config.json and config_model.py and monitors the 
directory set in confi_model.py > Settings.directory for newly created files.

If such was found, an Evenernote note is created and the file is attached. The new note is
tagged using the configuration from config.json.

## Usage

- Set the directory in **config_model.py**
- Read and follow instructions in **secrets/readme.md**
- Before first productive use you need to create oauth tokens by running **evernote_oauth.py**
- Start "python directory_monitor.py"

## Todos

- Write unit tests

- Last update: 2022-05-22