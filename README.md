# Scatter Plot Builder

Streamlit app for uploading CSV/Excel files and generating interactive, color-coded scatter plots.

## Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Run Tests

```bash
pytest -v
```

## Deploy to Azure App Service

Infrastructure uses **Linux App Service plan SKU F1** (free tier). **Always On is not available on F1** (only on Basic B1 and higher, which are paid). Run `terraform apply` once, then deploy code either manually or via GitHub Actions.

### 1. Provision infrastructure

```bash
cd terraform
terraform init
terraform apply
```

Note the outputs: `app_url`, `web_app_name`, `resource_group_name`.

### 2a. CI/CD: GitHub Actions (recommended)

Workflow: [.github/workflows/azure-app-service.yml](.github/workflows/azure-app-service.yml). On every push to `main` or `master` it runs `pytest`, then zip-deploys the repo to the Web App (Oryx builds from `requirements.txt` because `SCM_DO_BUILD_DURING_DEPLOYMENT` is set in Terraform).

**Azure (OpenID Connect, no publish profile secret):**

1. Entra ID → **App registrations** → New registration → note **Application (client) ID**, **Directory (tenant) ID**.
2. That app → **Certificates & secrets** → **Federated credentials** → Add **GitHub Actions** for this repository and branch (`main` or `master`).
3. Subscription → **Access control (IAM)** → **Add role assignment** → role **Website Contributor** (or **Contributor**) → assign to the app registration → scope = the resource group from `terraform output resource_group_name`.
4. GitHub → repo **Settings** → **Secrets and variables** → **Actions** → **New repository secrets**: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`.

If you changed Terraform `project` or `environment`, add repository variables `AZURE_WEBAPP_NAME` and `AZURE_RESOURCE_GROUP` matching `terraform output web_app_name` and `terraform output resource_group_name`. Otherwise the workflow defaults match `terraform/variables.tf`.

### 2b. Deploy application code manually

From the project root, zip and deploy:

```bash
zip -r app.zip app.py src/ requirements.txt .streamlit/
az webapp deploy \
  --resource-group scatter-app-prod-rg \
  --name scatter-app-prod-wa \
  --src-path app.zip \
  --type zip
```

(Replace resource group and app name with your `terraform output` values if they differ.)

### 3. Open the app

Visit the URL from `terraform output app_url`.

> **Note:** Free tier F1 has no always-on support. First request after idle will be slow (~30s cold start).
