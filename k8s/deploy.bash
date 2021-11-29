#!/bin/bash
# Deploy application to k8s.
# Usage: bash ./deploy.bash dev
#
# Requirements:
#   docker login git.expoforum.ru:5050
#   helm repo add euroskills http://chartmuseum.helm.expoforum.ru --username $HELM_USER --password $HELM_PASS

TAG=$1
NAME=qr-backend
NAMESPACE=euroskills-staging
IMAGE=git.expoforum.ru:5050/udb/qr-backend

SCRIPT_DIR=`dirname "$0"`

set -e

docker build $SCRIPT_DIR/.. -t $IMAGE -f $SCRIPT_DIR/../Dockerfile
docker tag $IMAGE $IMAGE:$TAG
docker push $IMAGE:$TAG

helm uninstall \
    "$NAME" \
    --namespace "$NAMESPACE" || true

helm upgrade \
    "$NAME" \
    euroskills/base-app \
	--set image.repository="$IMAGE" \
    --set image.tag="$TAG" \
	--namespace "$NAMESPACE" \
    --install \
	-f $SCRIPT_DIR/values.yaml


