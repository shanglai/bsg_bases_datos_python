#!/usr/bin/env bash
# =====================================================================
# c4_final_b6_valida_sql.sh
# Valida el SQL de la sesion contra BigQuery, SIN COBRAR.
#
# bq query --dry_run hace dos cosas:
#   comprueba la sintaxis y que las tablas y columnas existan
#   reporta cuantos bytes procesaria la consulta
# y no ejecuta nada, de modo que no genera cargo.
#
# Lo ejecuta el INSTRUCTOR antes de la clase, una sola vez.
#
# Uso:
#   ./c4_final_b6_valida_sql.sh MI_PROYECTO c4_final_b5_bigquery.sql
#
# Requisitos: gcloud y bq autenticados contra el proyecto de la clase.
# =====================================================================

set -uo pipefail

PROYECTO="${1:?Falta el identificador del proyecto}"
ARCHIVO="${2:-c4_final_b5_bigquery.sql}"

[ -f "$ARCHIVO" ] || { echo "No existe $ARCHIVO"; exit 1; }

TRABAJO=$(mktemp -d)
trap 'rm -rf "$TRABAJO"' EXIT

# Se sustituye el marcador y se quitan las lineas de comentario.
sed "s/PROYECTO/${PROYECTO}/g" "$ARCHIVO" | grep -v '^\s*--' > "$TRABAJO/sql"

# Se parte por punto y coma, una sentencia por archivo.
python3 - "$TRABAJO/sql" "$TRABAJO" <<'PY'
import sys, pathlib
texto = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
destino = pathlib.Path(sys.argv[2])
sentencias = [s.strip() for s in texto.split(";") if s.strip()]
for i, sentencia in enumerate(sentencias, 1):
    (destino / f"s{i:03d}.sql").write_text(sentencia, encoding="utf-8")
print(len(sentencias))
PY

TOTAL=$(ls "$TRABAJO"/s*.sql 2>/dev/null | wc -l)
echo "Sentencias a validar: $TOTAL"
echo "Proyecto: $PROYECTO"
echo

OK=0
FALLA=0
BYTES_TOTAL=0

for ARCHIVO_SQL in "$TRABAJO"/s*.sql; do
    NOMBRE=$(basename "$ARCHIVO_SQL" .sql)
    PRIMERA=$(head -c 68 "$ARCHIVO_SQL" | tr '\n' ' ' | tr -s ' ')

    SALIDA=$(bq query --use_legacy_sql=false --dry_run --project_id="$PROYECTO" \
             --format=json < "$ARCHIVO_SQL" 2>&1)
    CODIGO=$?

    if [ $CODIGO -eq 0 ]; then
        BYTES=$(echo "$SALIDA" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(int(d['statistics']['query']['totalBytesProcessed']))
except Exception:
    print(0)
" 2>/dev/null || echo 0)
        MB=$(python3 -c "print(f'{$BYTES/1024/1024:8.2f}')")
        BYTES_TOTAL=$((BYTES_TOTAL + BYTES))
        printf "  OK   %s %s MB  %s\n" "$NOMBRE" "$MB" "$PRIMERA"
        OK=$((OK + 1))
    else
        printf "  NO   %s              %s\n" "$NOMBRE" "$PRIMERA"
        echo "$SALIDA" | grep -iE "error|invalid|not found|syntax" | head -2 | sed 's/^/         /'
        FALLA=$((FALLA + 1))
    fi
done

echo
echo "======================================================================"
echo "Validas: $OK    Con error: $FALLA"
python3 -c "print(f'Total que procesaria la sesion completa: {$BYTES_TOTAL/1024/1024:.1f} MB')"
python3 -c "
gb = $BYTES_TOTAL/1024/1024/1024
print(f'Costo aproximado a 6.25 USD por TiB: {gb*6.25/1024:.6f} USD')
print()
print('El primer TiB de consultas al mes es gratuito, de modo que una')
print('sesion de este tamano no genera cargo alguno. La cifra se calcula')
print('para que el grupo vea el mecanismo, no porque importe aqui.')
"
echo "======================================================================"

[ $FALLA -eq 0 ] || exit 1
