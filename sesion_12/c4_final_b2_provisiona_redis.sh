#!/usr/bin/env bash
# =====================================================================
# c4_final_b2_provisiona_redis.sh
# Levanta el Redis de la clase en una VM de GCE, con un usuario por alumno.
#
# POR QUE UNA VM Y NO MEMORYSTORE
#   Memorystore vive dentro de una VPC. Los alumnos, conectandose desde
#   Cloud Shell o desde su equipo, NO lo alcanzan sin un conector
#   serverless, un bastion o una VPN. Ademas el nivel mas pequeno se
#   cobra por hora encendido.
#
#   Una e2-small con Redis 7 cuesta centavos por el dia de la clase, se
#   alcanza desde Cloud Shell, y permite crear un usuario por alumno con
#   ACL, que es de por si contenido de la sesion.
#
# SEGURIDAD
#   Este script abre el puerto 6379 SOLO a los rangos que se le indiquen.
#   NO usar 0.0.0.0/0. Un Redis abierto a internet se compromete en
#   minutos.
#
# Uso:
#   ./c4_final_b2_provisiona_redis.sh PROYECTO 20 "189.203.0.0/16"
#                                     proyecto  alumnos  rangos permitidos
# =====================================================================

set -euo pipefail

PROYECTO="${1:?Falta el identificador del proyecto}"
ALUMNOS="${2:-20}"
RANGOS="${3:?Falta el rango CIDR permitido. NO usar 0.0.0.0/0}"

ZONA="${ZONA:-us-central1-a}"
VM="curso-redis"

if [ "$RANGOS" = "0.0.0.0/0" ]; then
    echo "ERROR: no se permite 0.0.0.0/0. Indica el rango del aula."
    exit 1
fi

echo "Proyecto: $PROYECTO"
echo "Alumnos:  $ALUMNOS"
echo "Rangos:   $RANGOS"
echo

# ---------------------------------------------------------------------
# 1. Generar las credenciales de los alumnos
# ---------------------------------------------------------------------
python3 c4_final_b2_genera_acls.py "$ALUMNOS"

# ---------------------------------------------------------------------
# 2. Crear la VM
# ---------------------------------------------------------------------
echo "Creando la VM..."
gcloud compute instances create "$VM" \
    --project="$PROYECTO" \
    --zone="$ZONA" \
    --machine-type=e2-small \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --boot-disk-size=20GB \
    --tags=curso-redis \
    --metadata-from-file=startup-script=redis_startup.sh

# ---------------------------------------------------------------------
# 3. Regla de firewall, acotada
# ---------------------------------------------------------------------
echo "Creando la regla de firewall..."
gcloud compute firewall-rules create curso-redis-6379 \
    --project="$PROYECTO" \
    --allow=tcp:6379 \
    --source-ranges="$RANGOS" \
    --target-tags=curso-redis \
    --description="Redis del curso. Acotado al rango del aula." \
    || echo "  La regla ya existia."

# ---------------------------------------------------------------------
# 4. Esperar y aplicar las ACL
# ---------------------------------------------------------------------
echo "Esperando a que Redis arranque..."
sleep 45

echo "Aplicando las ACL de los alumnos..."
gcloud compute scp acl_alumnos.conf "$VM":/tmp/acl_alumnos.conf \
    --project="$PROYECTO" --zone="$ZONA"

gcloud compute ssh "$VM" --project="$PROYECTO" --zone="$ZONA" --command \
    "sudo bash -c 'cat /tmp/acl_alumnos.conf >> /etc/redis/users.acl && redis-cli -a \$(sudo grep -oP \"(?<=^requirepass ).*\" /etc/redis/redis.conf) --no-auth-warning ACL LOAD'"

IP=$(gcloud compute instances describe "$VM" --project="$PROYECTO" \
     --zone="$ZONA" --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo
echo "======================================================================"
echo "Redis listo en $IP:6379"
echo
echo "Credenciales de los alumnos: credenciales_alumnos.csv"
echo "Reparte una fila por persona."
echo
echo "Al terminar la clase, borrar todo:"
echo "  gcloud compute instances delete $VM --zone=$ZONA --project=$PROYECTO"
echo "  gcloud compute firewall-rules delete curso-redis-6379 --project=$PROYECTO"
echo "======================================================================"
