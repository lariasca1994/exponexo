#!/bin/bash
# Crea (o completa) la parte de ExpoNexo en Google Cloud para el servicio de pagos, dentro de la
# capa gratuita de Cloud Run y Artifact Registry:
#
#   proyecto <id> ─┬─ Artifact Registry "exponexo" (conserva solo las 2 imágenes más recientes)
#                  ├─ cuenta de ejecución exponexo-pagos-run (sin permisos sobre el proyecto)
#                  ├─ cuenta de despliegue exponexo-despliegue (Cloud Run + Artifact Registry)
#                  └─ Workload Identity Federation: solo el entorno `produccion` de este repositorio
#
# Cloud Run escala a cero; el servicio lo crea el primer despliegue del workflow de pagos.
# Requisitos: gcloud autenticado como dueño de la cuenta de facturación y GitHub CLI.
# Uso, desde la raíz del repositorio:   bash infra/gcp/crear.sh <id-del-proyecto> <región>
set -euo pipefail

PROYECTO=${1:?Indica el id del proyecto (nuevo o existente)}
REGION=${2:?Indica la región de Cloud Run}
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

echo "== Proyecto"
gcloud projects describe "$PROYECTO" >/dev/null 2>&1 || gcloud projects create "$PROYECTO" --name ExpoNexo
if [ -z "$(gcloud billing projects describe "$PROYECTO" --format 'value(billingAccountName)')" ]; then
  CUENTA_FACTURACION=$(gcloud billing accounts list --filter open=true --format 'value(name)' --limit 1)
  gcloud billing projects link "$PROYECTO" --billing-account "$CUENTA_FACTURACION" >/dev/null
fi
gcloud services enable run.googleapis.com artifactregistry.googleapis.com iamcredentials.googleapis.com \
  sts.googleapis.com --project "$PROYECTO"
NUMERO=$(gcloud projects describe "$PROYECTO" --format 'value(projectNumber)')

echo "== Artifact Registry con limpieza automática"
gcloud artifacts repositories describe exponexo --location "$REGION" --project "$PROYECTO" >/dev/null 2>&1 || \
  gcloud artifacts repositories create exponexo --repository-format docker --location "$REGION" --project "$PROYECTO"
POLITICA=$(mktemp)
cat > "$POLITICA" <<'JSON'
[
  {"name": "conservar-2-recientes", "action": {"type": "Keep"}, "mostRecentVersions": {"keepCount": 2}},
  {"name": "borrar-el-resto", "action": {"type": "Delete"}, "condition": {"tagState": "any"}}
]
JSON
gcloud artifacts repositories set-cleanup-policies exponexo --location "$REGION" --project "$PROYECTO" \
  --policy "$POLITICA" --no-dry-run >/dev/null
rm -f "$POLITICA"

echo "== Cuentas de servicio"
for cuenta in exponexo-pagos-run exponexo-despliegue; do
  gcloud iam service-accounts describe "$cuenta@$PROYECTO.iam.gserviceaccount.com" --project "$PROYECTO" >/dev/null 2>&1 || \
    gcloud iam service-accounts create "$cuenta" --project "$PROYECTO"
done
DESPLIEGUE="exponexo-despliegue@$PROYECTO.iam.gserviceaccount.com"
EJECUCION="exponexo-pagos-run@$PROYECTO.iam.gserviceaccount.com"
for rol in roles/run.admin roles/artifactregistry.writer; do
  gcloud projects add-iam-policy-binding "$PROYECTO" --member "serviceAccount:$DESPLIEGUE" --role "$rol" \
    --condition None >/dev/null
done
# El despliegue solo puede "actuar como" la cuenta de ejecución, no como otras
gcloud iam service-accounts add-iam-policy-binding "$EJECUCION" --project "$PROYECTO" \
  --member "serviceAccount:$DESPLIEGUE" --role roles/iam.serviceAccountUser >/dev/null

echo "== Federación con GitHub (sin llaves)"
gcloud iam workload-identity-pools describe github --location global --project "$PROYECTO" >/dev/null 2>&1 || \
  gcloud iam workload-identity-pools create github --location global --project "$PROYECTO" --display-name GitHub
gcloud iam workload-identity-pools providers describe github-oidc --workload-identity-pool github \
  --location global --project "$PROYECTO" >/dev/null 2>&1 || \
  gcloud iam workload-identity-pools providers create-oidc github-oidc --workload-identity-pool github \
    --location global --project "$PROYECTO" --issuer-uri https://token.actions.githubusercontent.com \
    --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.environment=assertion.environment" \
    --attribute-condition "assertion.repository == '$REPO' && assertion.environment == 'produccion'"
gcloud iam service-accounts add-iam-policy-binding "$DESPLIEGUE" --project "$PROYECTO" \
  --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/projects/$NUMERO/locations/global/workloadIdentityPools/github/attribute.repository/$REPO" >/dev/null

echo "== Valores para los workflows"
gh secret set GCP_PROJECT_ID --env produccion --repo "$REPO" --body "$PROYECTO"
gh secret set GCP_REGION --env produccion --repo "$REPO" --body "$REGION"
gh secret set GCP_SERVICE_ACCOUNT --env produccion --repo "$REPO" --body "$DESPLIEGUE"
gh secret set GCP_RUNTIME_SERVICE_ACCOUNT --env produccion --repo "$REPO" --body "$EJECUCION"
gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER --env produccion --repo "$REPO" \
  --body "projects/$NUMERO/locations/global/workloadIdentityPools/github/providers/github-oidc"
# URL determinista de Cloud Run: https://<servicio>-<número de proyecto>.<región>.run.app
gh variable set PAGOS_URL --env produccion --repo "$REPO" --body "https://exponexo-pagos-$NUMERO.$REGION.run.app"
echo "Listo: Google Cloud configurado."
