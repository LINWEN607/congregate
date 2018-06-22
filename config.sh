#!/bin/bash

#
# Bash script to generate configuration JSON for congregate
#

echo "##Configuring congregate"

echo "1. Host of parent instance (destination instance)"
read parent_instance_host
config=$(jq -n --arg i "$parent_instance_host" '{"parent_instance_host": $i}')

echo "2. Access token to use for parent instance"
read parent_instance_token
config=$(echo $config | jq --arg i "$parent_instance_token" '. + {parent_instance_token: $i}')

echo "3. Host of child instance (destination instance)"
read child_instance_host
config=$(echo $config | jq --arg i "$child_instance_host" '. + {child_instance_host: $i}')

echo "4. Access token to use for child instance"
read child_instance_token
config=$(echo $config | jq --arg i "$child_instance_token" '. + {child_instance_token: $i}')

config=$(jq -n --argjson i "$config" '{config: $i}')
echo $config | jq . > config.json

echo "Congregate has been successfully configured"
