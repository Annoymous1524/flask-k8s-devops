#!/bin/bash

echo "🚀 Pulling latest image..."
docker pull dkbhowmik0/flask-k8s-devops:latest

echo "🔄 Restarting Kubernetes deployment..."
kubectl rollout restart deployment flask-app

echo "✅ Deployment updated!"
