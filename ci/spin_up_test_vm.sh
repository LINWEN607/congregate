#!/bin/bash

spin_up_instance () {
    poetry run aws ec2 run-instances \
        --image-id $AMI_ID \
        --count 1 \
        --instance-type c5a.xlarge \
        --key-name $KEY_NAME \
        --security-group-ids $SECURITY_GROUP
}

get_instance_ip () {
    poetry run aws ec2 describe-instances --instance-ids $INSTANCE_ID | jq '.Reservations[0].Instances[0].NetworkInterfaces[0].Association.PublicIp' | tr -d '\n' | sed -e 's/^"//' -e 's/"$//' 
}

get_latest_version () {
    curl --header "PRIVATE-TOKEN: $ACCESS_TOKEN" https://gitlab.com/api/v4/version | jq -r '. | "\(.version)"'
}

get_ami_id () {
    poetry run aws ec2 describe-images --filters "Name=name,Values=GitLab Seed Image-$(get_latest_version)" | jq -r '.Images[0].ImageId'
}

echo "Getting AMI ID"
AMI_ID=$(get_ami_id)
echo $AMI_ID

echo "Spinning up instance"
INSTANCE_ID=$(spin_up_instance | jq '.Instances[0].InstanceId' | tr -d '\n' | sed -e 's/^"//' -e 's/"$//')

echo $INSTANCE_ID > instance_id

echo $(get_instance_ip)

while [[ $(get_instance_ip) == "null" ]]; do
    echo "Waiting for instance to start"
    sleep 5
done

printf "$(get_instance_ip)" > source_ip
