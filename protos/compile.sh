#!/bin/bash

#
# Usage: cd into this directory and then run this script
# 

# Iterating over all .proto files to generate gRPC python files
for PROTOBUF in $(ls *.proto)
do
    SRC="${PROTOBUF%%.*}"
    COMPILE_PATH="../congregate/migration/$SRC"
    if [ ! -d $COMPILE_PATH ]; then
        echo "No corresponding file for **$SRC** python files found. Creating now"
        mkdir -p $COMPILE_PATH
    fi
    echo "Compiling **$SRC** gRPC files"
    poetry run python -m grpc_tools.protoc --proto_path=. --python_out=$COMPILE_PATH --grpc_python_out=$COMPILE_PATH ./$PROTOBUF
    mkdir -p ../docker/$SRC
    # Iterating over generated gRPC python files to symlink to the docker server images
    echo "Generating **$SRC** gRPC symlinks"
    for RPC_FILE in $(ls $COMPILE_PATH/*pb2*)
    do
        LN_NAME="../docker/$SRC/$(basename $RPC_FILE)"
        if [ ! -L "$LN_NAME" ]; then
            echo "Symbolic link for $RPC_FILE does not exist. Creating it now"
            ln -s $RPC_FILE $LN_NAME
        else
            echo "Symbolic link already exists for $RPC_FILE. Skipping"
        fi
    done
    echo "**$SRC** gRPC files have been generated. Be sure to check the imports of $COMPILE_PATH/${SRC}_pb2_grpc.py. The imports will be different between the server and the client usage"
done

