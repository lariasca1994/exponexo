#!/bin/bash
# Crea (o completa) la parte de ExpoNexo en Azure, dentro de la asignación gratuita mensual de
# Azure Container Apps (plan de consumo, escala a cero):
#
#   entorno exponexo-env (sin Log Analytics, que cobra por ingesta)
#     ├─ exponexo-identidad-reservas (puerto 8001)
#     └─ exponexo-mesa-ayuda         (puerto 8003)
#
# Las apps arrancan con una imagen de muestra; el primer push de cada servicio las reemplaza.
# También crea la identidad que usa GitHub por OIDC (sin contraseñas), con permiso solo sobre el
# grupo de recursos, y guarda en el entorno `produccion` de GitHub los valores de los workflows.
#
# Requisitos: Azure CLI con la extensión containerapp, GitHub CLI y un token clásico de GitHub con
# permiso read:packages (para que Azure descargue las imágenes privadas de GHCR).
# Uso, desde la raíz del repositorio:   bash infra/azure/crear.sh <grupo-de-recursos>
set -euo pipefail
export MSYS_NO_PATHCONV=1

GRUPO=${1:?Indica el grupo de recursos (ya creado)}
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
DUENO=${REPO%%/*}
UBICACION=$(az group show --name "$GRUPO" --query location --output tsv)
SUSCRIPCION=$(az account show --query id --output tsv)
INQUILINO=$(az account show --query tenantId --output tsv)
ENTORNO=exponexo-env

echo "== Entorno de Container Apps"
az containerapp env show --name "$ENTORNO" --resource-group "$GRUPO" >/dev/null 2>&1 || \
  az containerapp env create --name "$ENTORNO" --resource-group "$GRUPO" --location "$UBICACION" \
    --logs-destination none --only-show-errors --output none

read -r -s -p "Token de GitHub con read:packages (Enter para conservar el ya configurado): " TOKEN_GHCR; echo
if [ -n "$TOKEN_GHCR" ]; then
  gh secret set GHCR_READ_TOKEN --env produccion --repo "$REPO" --body "$TOKEN_GHCR"
fi

declare -A PUERTOS=([identidad-reservas]=8001 [mesa-ayuda]=8003)
declare -A VARIABLES=([identidad-reservas]=IDENTIDAD_URL [mesa-ayuda]=MESA_AYUDA_URL)
for servicio in identidad-reservas mesa-ayuda; do
  APP="exponexo-$servicio"
  echo "== $APP"
  if ! az containerapp show --name "$APP" --resource-group "$GRUPO" >/dev/null 2>&1; then
    az containerapp create --name "$APP" --resource-group "$GRUPO" --environment "$ENTORNO" \
      --image mcr.microsoft.com/k8se/quickstart:latest --ingress external \
      --target-port "${PUERTOS[$servicio]}" --min-replicas 0 --max-replicas 1 \
      --cpu 0.5 --memory 1.0Gi --only-show-errors --output none
  fi
  if [ -n "$TOKEN_GHCR" ]; then
    az containerapp registry set --name "$APP" --resource-group "$GRUPO" --server ghcr.io \
      --username "$DUENO" --password "$TOKEN_GHCR" --only-show-errors --output none
  fi
  FQDN=$(az containerapp show --name "$APP" --resource-group "$GRUPO" \
    --query properties.configuration.ingress.fqdn --output tsv)
  gh variable set "${VARIABLES[$servicio]}" --env produccion --repo "$REPO" --body "https://$FQDN"
done
unset TOKEN_GHCR

echo "== Identidad de despliegue para GitHub (OIDC)"
APP_ID=$(az ad app list --display-name exponexo-github-despliegue --query '[0].appId' --output tsv)
if [ -z "$APP_ID" ]; then
  APP_ID=$(az ad app create --display-name exponexo-github-despliegue --query appId --output tsv)
  az ad sp create --id "$APP_ID" --output none
fi
# GitHub firma el token con el sujeto clásico (dueño/repo) o con el que incluye los IDs numéricos
# (dueño@id/repo@id); se registran ambos para que el inicio de sesión funcione en los dos casos.
IDS=$(gh api "repos/$REPO" -q '"\(.owner.login)@\(.owner.id)/\(.name)@\(.id)"')
declare -A SUJETOS=([github-produccion]="repo:$REPO:environment:produccion" [github-produccion-ids]="repo:$IDS:environment:produccion")
for nombre in "${!SUJETOS[@]}"; do
  EXISTE=$(az ad app federated-credential list --id "$APP_ID" --query "[?name=='$nombre'] | length(@)" --output tsv)
  if [ "$EXISTE" = "0" ]; then
    az ad app federated-credential create --id "$APP_ID" --parameters "{
      \"name\": \"$nombre\",
      \"issuer\": \"https://token.actions.githubusercontent.com\",
      \"subject\": \"${SUJETOS[$nombre]}\",
      \"audiences\": [\"api://AzureADTokenExchange\"]}" --output none
  fi
done
for intento in 1 2 3 4 5 6; do   # el principal recién creado tarda en verse
  az role assignment create --assignee "$APP_ID" --role Contributor \
    --scope "/subscriptions/$SUSCRIPCION/resourceGroups/$GRUPO" --only-show-errors --output none && break
  [ "$intento" = 6 ] && exit 1
  sleep 10
done

echo "== Valores para los workflows"
gh secret set AZURE_CLIENT_ID --env produccion --repo "$REPO" --body "$APP_ID"
gh secret set AZURE_TENANT_ID --env produccion --repo "$REPO" --body "$INQUILINO"
gh secret set AZURE_SUBSCRIPTION_ID --env produccion --repo "$REPO" --body "$SUSCRIPCION"
gh secret set AZURE_RESOURCE_GROUP --env produccion --repo "$REPO" --body "$GRUPO"
echo "Listo: Azure configurado."
