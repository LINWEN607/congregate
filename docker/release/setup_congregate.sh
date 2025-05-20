#!/bin/bash

#
# Congregate Docker Compose setup script
#
# This script sets up the directories and downloads the necessary
# files for running Congregate Docker Compose.
#
# This script assumes you are running as sudo su
#
# Usage: ./setup_congregate.sh
#

main() {
    folders=(
        "congregate-data"
        "congregate-data/congregate-data"
        "congregate-data/congregate-data/logs"
        "congregate-data/mongo-data"
        "congregate-data/redis-cache"
        "congregate-data/loki-data"
    )

    log_files=(
        "gunicorn.log"
        "gunicorn_err.log"
        "celery.log"
        "celery_err.log"
        "flower.log"
        "flower_err.log"
        "congregate.log"
        "congregate_log.json"
        "application.log"
    )

    echo "Creating Congregate data directories"
    for folder in "${folders[@]}"; do
        create_folder $folder
   
    )

    echo "Seeding Congregate log files"
    for log_file in "${log_files[@]}"; do
        touch "congregate-data/congregate-data/logs/$log_file"
    done

    echo "Downloading Congregate Docker Compose file"
    check_for_wget
    wget -q --show-progress https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/raw/master/docker/release/docker-compose.yml

    echo "Downloading Grafana configuration files"
    mkdir -p congregate-data/grafana_provisioning/dashboards
    wget -q --show-progress https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/raw/master/docker/grafana_provisioning/dashboards/dashboards.yml -O congregate-data/grafana_provisioning/dashboards/dashboards.yml
    mkdir -p congregate-data/grafana_provisioning/datasources
    wget -q --show-progress https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/raw/master/docker/grafana_provisioning/datasources/loki.yml -O congregate-data/grafana_provisioning/datasources/loki.yml
    mkdir -p congregate-data/grafana_dashboards
    wget -q --show-progress https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/raw/master/docker/grafana_dashboards/logs.json -O congregate-data/grafana_dashboards/logs.json

    echo "Downloading Loki configuration"
    wget https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/raw/master/docker/loki-config.yaml -O congregate-data/loki-config.yaml

    echo "Downloading Vector configuration"
    wget -q --show-progress https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/raw/master/docker/vector.yaml -O congregate-data/vector.yaml

    echo "Setting environment variable for Congregate data directory"
    echo "export CONGREGATE_DATA=$(pwd)/congregate-data" >> ~/.bashrc
    
    echo "*********************************************"
    echo "PLEASE EXPLICITLY SOURCE YOUR ~/.bashrc FILE:"
    echo "source ~/.bashrc"
    echo "-"
    echo "OR RUN THE FOLLOWING EXPORT COMMAND:"
    echo "export CONGREGATE_DATA=$(pwd)/congregate-data"
    echo "-"
    echo "You will also need to run"
    echo "chmod -R a+rwx congregate-data/"
    echo "*********************************************"

    echo "Congregate setup script completed successfully"
}

## Helper functions

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

check_for_wget () {
    if ! command_exists "wget"; then
        echo "wget is missing."
        echo "Installing wget..."
        if [ "$(uname)" == "Darwin" ]; then
        brew install wget
        elif [ "$(uname)" == "Linux" ]; then
        if [ -f /etc/os-release ]; then
                . /etc/os-release
                case $ID in
                debian|ubuntu)
                    sudo apt-get install wget
                    ;;
                rhel|centos|fedora)
                    sudo yum install wget
                    ;;
                *)
                    echo "Unsupported Linux distribution: $ID"
                    exit 1
                    ;;
                esac
            else
                echo "Unsupported platform" # handle other unsupported platforms here if necessary
                exit 1
            fi
        else
        echo "Unsupported platform: $(uname)"
        exit 1
        fi
    fi
}

create_folder() {
    echo "Creating directory: $1"
    mkdir -p "$1"
}

## Calling the main function

main
