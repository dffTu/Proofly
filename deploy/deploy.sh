#!/bin/bash
set -e

HOST="ubuntu@158.160.106.142"
REMOTE_DIR="~/proofly"

echo "==> Syncing code to server..."
rsync -az --delete \
  --exclude='.venv*' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='terraform/.terraform' \
  --exclude='terraform/terraform.tfstate*' \
  --exclude='.env' \
  . "$HOST:$REMOTE_DIR/"

echo "==> Building and starting containers..."
ssh "$HOST" "cd $REMOTE_DIR && docker compose -f docker-compose.prod.yml up --build -d"

echo "==> Waiting for web container to start..."
sleep 5

echo "==> Collecting static files..."
ssh "$HOST" "cd $REMOTE_DIR && docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput"
ssh "$HOST" "docker cp \$(docker compose -f $REMOTE_DIR/docker-compose.prod.yml ps -q web):/app/staticfiles $REMOTE_DIR/staticfiles"

echo "==> Fixing permissions for nginx..."
ssh "$HOST" "chmod o+x /home/ubuntu && chmod -R o+rX $REMOTE_DIR/staticfiles"

echo "==> Updating nginx config..."
ssh "$HOST" "sudo cp $REMOTE_DIR/deploy/nginx.conf /etc/nginx/sites-available/proofly && \
             sudo ln -sf /etc/nginx/sites-available/proofly /etc/nginx/sites-enabled/proofly && \
             sudo rm -f /etc/nginx/sites-enabled/default && \
             sudo nginx -t && sudo systemctl reload nginx"

echo "==> Done! https://proofly.ganvas.ru"
