#!/bin/bash

# nginx/init-letsencrypt.sh
# Ejecutar UNA SOLA VEZ para obtener el certificado SSL inicial

domains=(mindmetrics.cloud www.mindmetrics.cloud)  
rsa_key_size=4096
data_path="./certbot"
email="mindmetricsinfra@hotmail.com"  
staging=0  

if [ -d "$data_path" ]; then
  read -p "⚠️ Ya existe una carpeta 'certbot'. ¿Borrar y continuar? (y/N) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$data_path"
  else
    exit 1
  fi
fi

mkdir -p "$data_path/www"
mkdir -p "$data_path/conf/live/$domains"

# Obtener certificado de prueba (si staging=1)
if [ $staging != "0" ]; then staging_arg="--staging"; fi

docker-compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $staging_arg \
    --email $email \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --no-eff-email \
    -d ${domains[0]} -d ${domains[1]}" certbot

echo "✅ Certificado obtenido. Ahora inicia los servicios: docker-compose up -d"