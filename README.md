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

### 1. Provision infrastructure

```bash
cd terraform
terraform init
terraform apply
```

Note the `app_url` output.

### 2. Deploy application code

From the project root, zip and deploy:

```bash
zip -r app.zip app.py src/ requirements.txt .streamlit/
az webapp deploy \
  --resource-group scatter-app-prod-rg \
  --name scatter-app-prod-wa \
  --src-path app.zip \
  --type zip
```

### 3. Open the app

Visit the URL printed by `terraform output app_url`.

> **Note:** Free tier F1 has no always-on support. First request after idle will be slow (~30s cold start).
