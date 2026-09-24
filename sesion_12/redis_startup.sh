#!/bin/bash
# Script de arranque de la VM. Instala Redis y lo deja escuchando.
apt-get update -q
apt-get install -y -q redis-server

CLAVE_ADMIN=$(openssl rand -hex 24)

cat > /etc/redis/redis.conf <<CONF
bind 0.0.0.0
port 6379
protected-mode yes
requirepass ${CLAVE_ADMIN}
aclfile /etc/redis/users.acl
maxmemory 512mb
maxmemory-policy allkeys-lru
appendonly no
save ""
CONF

# El archivo de ACL debe existir antes de arrancar.
cat > /etc/redis/users.acl <<ACL
user default on >${CLAVE_ADMIN} ~* &* +@all
ACL

chown redis:redis /etc/redis/users.acl /etc/redis/redis.conf
chmod 640 /etc/redis/users.acl

systemctl restart redis-server
systemctl enable redis-server

echo "${CLAVE_ADMIN}" > /root/clave_admin.txt
chmod 600 /root/clave_admin.txt
