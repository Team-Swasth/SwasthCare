# SwasthCare ![Django](https://img.shields.io/badge/Django-%23092E20.svg?logo=django&logoColor=white) ![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff) ![Azure](https://img.shields.io/badge/Azure-%230072C6.svg?logo=microsoft-azure&logoColor=white) ![MongoDB](https://img.shields.io/badge/MongoDB-47A248?logo=mongodb&logoColor=white) ![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)

SwasthCare is a comprehensive platform designed to empower consumers and sellers by providing transparency in product information. It leverages Azure services for AI-powered analysis, document intelligence, and communication.

## Features

- **Consumer Dashboard**: Scan barcodes to access detailed product information, including nutritional data, ingredients, and allergen warnings.
- **Seller Dashboard**: Upload product images for AI-powered analysis and manage product data.
- **AI Integration**: Extract product details from images using Azure Document Intelligence.
- **Chatbot**: Ask questions about products using a built-in chatbot.
- **Secure Authentication**: User registration, login, and profile management.

---

## Prerequisites

- Python 3.8+
- Azure CLI installed and logged in
- Azure subscription with appropriate permissions
- PostgreSQL and MongoDB databases

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Team-Swasth/SwasthCare.git
cd SwasthCare
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory and add the following:

```bash
DB_NAME="DATABASE_NAME"
DB_USER="DATABASE_USER"
DB_PASSWORD="DB_PASSWORD"
DB_HOST="YOUR_DATABASE_HOST"
DB_PORT="DATABASE_CONN_PORT"

COSMOS_CONN_STRING="COSMOS_CONNECTION_STRING"
AZURE_DI_ENDPOINT="AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"
AZURE_DI_API_KEY="AZURE_DOCUMENT_INTELLIGENCE_API_KEY"
AZURE_AI_ENDPOINT="AZURE_AI_SERVICE_ENDPOINT"
AZURE_AI_API_KEY="AZURE_AI_SERVICE_API_KEY"

SECRET_KEY="YOUR_DJANGO_SECRET_KEY"

AZURE_COMMUNICATION_CONNECTION_STRING="YOUR_AZURE_COMMUNICATION_CONNECTION_STRING"
AZURE_COMMUNICATION_FROM_EMAIL="YOUR_AZURE_COMMUNICATION_FROM_EMAIL"
```

### 4. Apply Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create a Superuser

```bash
python manage.py createsuperuser
```

### 6. Run the Development Server

```bash
python manage.py runserver
```

Access the application at `http://localhost:8000` on your browser.

---

## Usage

### Consumer Features

- **Scan Product**: Navigate to the Consumer Dashboard and scan a product barcode.
- **View Product Details**: Access detailed nutritional information, ingredients, and allergen warnings.

### Seller Features

- **Upload Product Images**: Use the Seller Dashboard to upload product images for AI analysis.
- **Manage Products**: Edit and update product details.

---

## Azure Services Used

- **Azure Document Intelligence**: Extract product details from images.
- **Azure AI Services**: Power the chatbot and other AI features.
- **Azure Communication Services**: Enable email notifications.

---

## Owners (Team Swasth)

- [Saksham Kumar](https://github.com/Polymath-Saksh)
- [Aloukik Joshi](https://github.com/aloukikjoshi)
- [Rhythm Narang](https://github.com/rhythmnarang1)
- [Anisha Dua](https://github.com/anishadua)

## License

This project is licensed under the [Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0)](LICENSE), which permits others to share and adapt the material for non-commercial purposes, provided that appropriate credit is given to the original author.
