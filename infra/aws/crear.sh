#!/bin/bash
# Crea (o completa, si ya existe) la infraestructura de eventos de ExpoNexo en AWS, dentro de la capa
# gratuita permanente de SNS, SQS y Lambda:
#
#   tema SNS exponexo-eventos ──► cola exponexo-repartidor (+ DLQ) ──► Lambda exponexo-repartidor
#                             └─► cola exponexo-avisos     (+ DLQ) ──► Lambda exponexo-avisos
#
# También crea el rol que asume GitHub por OIDC para desplegar las funciones y un usuario que SOLO
# puede publicar en el tema (lo usan identidad, pagos y mesa de ayuda, que corren fuera de AWS).
# Al final guarda en el entorno `produccion` de GitHub los valores que necesitan los workflows.
#
# Requisitos: AWS CLI con permisos de administrador, GitHub CLI autenticado y región configurada.
# Uso, desde la raíz del repositorio:   bash infra/aws/crear.sh
set -euo pipefail
export MSYS_NO_PATHCONV=1   # Git Bash en Windows no debe reescribir ARN ni rutas de logs

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
REGION=$(aws configure get region)
CUENTA=$(aws sts get-caller-identity --query Account --output text)
TEMA=exponexo-eventos
FUNCIONES=(repartidor avisos)

echo "== Tema SNS"
TEMA_ARN=$(aws sns create-topic --name "$TEMA" --query TopicArn --output text)

for f in "${FUNCIONES[@]}"; do
  echo "== Colas de $f"
  DLQ_URL=$(aws sqs create-queue --queue-name "exponexo-$f-dlq" \
    --attributes MessageRetentionPeriod=1209600 --query QueueUrl --output text)
  DLQ_ARN=$(aws sqs get-queue-attributes --queue-url "$DLQ_URL" --attribute-names QueueArn \
    --query Attributes.QueueArn --output text)
  COLA_URL=$(aws sqs create-queue --queue-name "exponexo-$f" --query QueueUrl --output text)
  COLA_ARN=$(aws sqs get-queue-attributes --queue-url "$COLA_URL" --attribute-names QueueArn \
    --query Attributes.QueueArn --output text)
  # Tras 5 intentos fallidos el mensaje pasa a la DLQ; solo el tema puede escribir en la cola
  python3 - "$COLA_URL" "$COLA_ARN" "$DLQ_ARN" "$TEMA_ARN" <<'PY'
import json, subprocess, sys
cola_url, cola_arn, dlq_arn, tema_arn = sys.argv[1:]
politica = {"Version": "2012-10-17", "Statement": [{
    "Effect": "Allow", "Principal": {"Service": "sns.amazonaws.com"}, "Action": "sqs:SendMessage",
    "Resource": cola_arn, "Condition": {"ArnEquals": {"aws:SourceArn": tema_arn}}}]}
atributos = {
    "VisibilityTimeout": "180",
    "MessageRetentionPeriod": "345600",
    "RedrivePolicy": json.dumps({"deadLetterTargetArn": dlq_arn, "maxReceiveCount": "5"}),
    "Policy": json.dumps(politica),
}
subprocess.run(["aws", "sqs", "set-queue-attributes", "--queue-url", cola_url,
                "--attributes", json.dumps(atributos)], check=True)
PY
  aws sns subscribe --topic-arn "$TEMA_ARN" --protocol sqs --notification-endpoint "$COLA_ARN" \
    --attributes RawMessageDelivery=true --return-subscription-arn >/dev/null

  echo "== Rol de ejecución de $f"
  ROL="exponexo-lambda-$f"
  if ! aws iam get-role --role-name "$ROL" >/dev/null 2>&1; then
    aws iam create-role --role-name "$ROL" --assume-role-policy-document \
      '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' >/dev/null
    sleep 10   # IAM tarda unos segundos en propagar el rol nuevo
  fi
  aws iam put-role-policy --role-name "$ROL" --policy-name ejecucion --policy-document "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [
      {\"Effect\": \"Allow\", \"Action\": [\"sqs:ReceiveMessage\", \"sqs:DeleteMessage\", \"sqs:GetQueueAttributes\"], \"Resource\": \"$COLA_ARN\"},
      {\"Effect\": \"Allow\", \"Action\": [\"logs:CreateLogStream\", \"logs:PutLogEvents\"], \"Resource\": \"arn:aws:logs:$REGION:$CUENTA:log-group:/aws/lambda/exponexo-$f:*\"}
    ]}"

  echo "== Función exponexo-$f"
  if ! aws lambda get-function --function-name "exponexo-$f" >/dev/null 2>&1; then
    # Código inicial mínimo: el workflow de eventos lo reemplaza en el primer despliegue
    TMP=$(mktemp -d)
    mkdir -p "$TMP/$f" && : > "$TMP/$f/__init__.py"
    printf 'def handler(event, context=None):\n    return {"batchItemFailures": []}\n' > "$TMP/$f/funcion.py"
    (cd "$TMP" && python3 -c "import shutil; shutil.make_archive('codigo', 'zip', '.', '$f')")
    ZIP="$TMP/codigo.zip"
    # En Git Bash (Windows) la AWS CLI necesita la ruta en formato Windows
    command -v cygpath >/dev/null && ZIP=$(cygpath -w "$ZIP")
    for intento in 1 2 3 4 5 6; do   # el rol recién creado puede tardar en ser asumible
      aws lambda create-function --function-name "exponexo-$f" --runtime python3.14 \
        --handler "$f.funcion.handler" --role "arn:aws:iam::$CUENTA:role/$ROL" \
        --zip-file "fileb://$ZIP" --timeout 30 --memory-size 256 >/dev/null && break
      [ "$intento" = 6 ] && exit 1
      sleep 10
    done
    rm -rf "$TMP"
    aws lambda wait function-active-v2 --function-name "exponexo-$f"
  fi
  aws logs create-log-group --log-group-name "/aws/lambda/exponexo-$f" 2>/dev/null || true
  aws logs put-retention-policy --log-group-name "/aws/lambda/exponexo-$f" --retention-in-days 14
  if [ "$(aws lambda list-event-source-mappings --function-name "exponexo-$f" --event-source-arn "$COLA_ARN" \
        --query 'length(EventSourceMappings)' --output text)" = "0" ]; then
    aws lambda create-event-source-mapping --function-name "exponexo-$f" --event-source-arn "$COLA_ARN" \
      --batch-size 10 --function-response-types ReportBatchItemFailures >/dev/null
  fi
done

echo "== Rol de despliegue para GitHub (OIDC)"
PROVEEDOR="arn:aws:iam::$CUENTA:oidc-provider/token.actions.githubusercontent.com"
aws iam get-open-id-connect-provider --open-id-connect-provider-arn "$PROVEEDOR" >/dev/null 2>&1 || \
  aws iam create-open-id-connect-provider --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com >/dev/null
ROL_DESPLIEGUE=exponexo-github-despliegue
CONFIANZA="{
  \"Version\": \"2012-10-17\",
  \"Statement\": [{\"Effect\": \"Allow\", \"Principal\": {\"Federated\": \"$PROVEEDOR\"},
    \"Action\": \"sts:AssumeRoleWithWebIdentity\",
    \"Condition\": {\"StringEquals\": {\"token.actions.githubusercontent.com:aud\": \"sts.amazonaws.com\",
      \"token.actions.githubusercontent.com:sub\": \"repo:$REPO:environment:produccion\"}}}]}"
if aws iam get-role --role-name "$ROL_DESPLIEGUE" >/dev/null 2>&1; then
  aws iam update-assume-role-policy --role-name "$ROL_DESPLIEGUE" --policy-document "$CONFIANZA"
else
  aws iam create-role --role-name "$ROL_DESPLIEGUE" --assume-role-policy-document "$CONFIANZA" >/dev/null
fi
aws iam put-role-policy --role-name "$ROL_DESPLIEGUE" --policy-name desplegar-funciones --policy-document "{
  \"Version\": \"2012-10-17\",
  \"Statement\": [
    {\"Effect\": \"Allow\", \"Action\": [\"lambda:UpdateFunctionCode\", \"lambda:UpdateFunctionConfiguration\", \"lambda:GetFunction\", \"lambda:GetFunctionConfiguration\"],
     \"Resource\": [\"arn:aws:lambda:$REGION:$CUENTA:function:exponexo-repartidor\", \"arn:aws:lambda:$REGION:$CUENTA:function:exponexo-avisos\"]},
    {\"Effect\": \"Allow\", \"Action\": [\"logs:CreateLogGroup\", \"logs:PutRetentionPolicy\"],
     \"Resource\": \"arn:aws:logs:$REGION:$CUENTA:log-group:/aws/lambda/exponexo-*\"}
  ]}"

echo "== Usuario que solo publica en el tema"
USUARIO=exponexo-publicador
aws iam get-user --user-name "$USUARIO" >/dev/null 2>&1 || aws iam create-user --user-name "$USUARIO" >/dev/null
aws iam put-user-policy --user-name "$USUARIO" --policy-name publicar-eventos --policy-document \
  "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":\"sns:Publish\",\"Resource\":\"$TEMA_ARN\"}]}"
if [ "$(aws iam list-access-keys --user-name "$USUARIO" --query 'length(AccessKeyMetadata)' --output text)" = "0" ]; then
  # La llave nueva va directo a GitHub sin mostrarse en pantalla
  aws iam create-access-key --user-name "$USUARIO" --output json | python3 -c "
import json, subprocess, sys
llave = json.load(sys.stdin)['AccessKey']
for nombre, valor in (('EVENTOS_AWS_ACCESS_KEY_ID', llave['AccessKeyId']), ('EVENTOS_AWS_SECRET_ACCESS_KEY', llave['SecretAccessKey'])):
    subprocess.run(['gh', 'secret', 'set', nombre, '--env', 'produccion', '--repo', '$REPO'], input=valor, text=True, check=True)
print('Llave del publicador guardada en GitHub')"
else
  echo "El publicador ya tiene llave (para rotarla: borra la anterior y vuelve a correr este script)"
fi

echo "== Valores para los workflows"
gh secret set AWS_ROLE_ARN --env produccion --repo "$REPO" --body "arn:aws:iam::$CUENTA:role/$ROL_DESPLIEGUE"
gh secret set AWS_REGION --env produccion --repo "$REPO" --body "$REGION"
gh variable set AWS_REGION --env produccion --repo "$REPO" --body "$REGION"
gh variable set SNS_TEMA_EVENTOS_ARN --env produccion --repo "$REPO" --body "$TEMA_ARN"
echo "Listo: AWS configurado."
