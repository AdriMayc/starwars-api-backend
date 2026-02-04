param(
  [string]$PROJECT_ID = $env:PROJECT_ID,
  [string]$REGION = $(if ($env:REGION) { $env:REGION } else { "us-central1" }),
  [string]$FUNC_NAME = $(if ($env:FUNC_NAME) { $env:FUNC_NAME } else { "starwars-api" }),
  [string]$API_ID = $(if ($env:API_ID) { $env:API_ID } else { "starwars-api" }),
  [string]$API_CFG = $(if ($env:API_CFG) { $env:API_CFG } else { ("starwars-cfg-" + (Get-Date -Format "yyyyMMdd-HHmmss")) }),
  [string]$GW_ID = $(if ($env:GW_ID) { $env:GW_ID } else { "starwars-gw" })
)

if (-not $PROJECT_ID) { throw "Defina PROJECT_ID. Ex: `$env:PROJECT_ID='smiling-landing-473618-j8'" }

Write-Host "Project: $PROJECT_ID"
gcloud config set project $PROJECT_ID | Out-Host

# Enable required APIs
gcloud services enable `
  cloudfunctions.googleapis.com `
  cloudbuild.googleapis.com `
  artifactregistry.googleapis.com `
  apigateway.googleapis.com `
  servicemanagement.googleapis.com `
  servicecontrol.googleapis.com | Out-Host

# Deploy Cloud Function Gen2
Write-Host "Deploying Cloud Function..."
gcloud functions deploy $FUNC_NAME `
  --gen2 `
  --runtime=python311 `
  --region=$REGION `
  --source=src `
  --entry-point=main `
  --trigger-http `
  --allow-unauthenticated | Out-Host

$FUNC_URL = (gcloud functions describe $FUNC_NAME --gen2 --region=$REGION --format="value(serviceConfig.uri)")
Write-Host "Function URL: $FUNC_URL"

# Render OpenAPI for Gateway
Write-Host "Rendering openapi-gateway..."
(Get-Content openapi-gateway.yaml -Raw).Replace('${FUNC_URL}', $FUNC_URL) | Set-Content openapi-gateway.rendered.yaml -NoNewline

# Create API (ignore if exists)
Write-Host "Creating API (if needed)..."
try { gcloud api-gateway apis create $API_ID --project=$PROJECT_ID | Out-Host } catch { }

# Create new API config (configs are immutable -> must be unique)
Write-Host "Creating API config..."
gcloud api-gateway api-configs create $API_CFG `
  --api=$API_ID `
  --openapi-spec=openapi-gateway.rendered.yaml `
  --project=$PROJECT_ID | Out-Host

# Create Gateway (ignore if exists)
Write-Host "Creating Gateway (if needed)..."
try {
  gcloud api-gateway gateways create $GW_ID `
    --api=$API_ID `
    --api-config=$API_CFG `
    --location=$REGION `
    --project=$PROJECT_ID | Out-Host
} catch { }

$GW_HOST = (gcloud api-gateway gateways describe $GW_ID --location=$REGION --format="value(defaultHostname)")
Write-Host "Gateway URL: https://$GW_HOST"
Write-Host "Done."
