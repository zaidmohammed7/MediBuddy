# MediBuddy - AI-Powered Healthcare Assistant 🏥

MediBuddy is a full-stack healthcare platform designed to bridge structured medical data with generative AI insights. It provides users with preliminary diagnosis support by analyzing symptoms against a validated medical ontology and offering AI-driven summaries.

## 🚀 Key Features

* **AI-Powered Diagnosis:** Integrates **Google Gemini API** to generate human-readable medical summaries and preliminary diagnostic insights based on user symptoms.
* **Robust Data Architecture:** Utilizes a complex **MySQL** schema to map many-to-many relationships between symptoms and diseases.
* **Transactional Integrity:** Implements **ACID-compliant transactions** to ensure data consistency during multi-step medical record updates.
* **Data Validation:** Features a strict validation pipeline using regex and set logic to verify medical data against a predefined ontology before storage.
* **Doctor Finder:** Locates specialists based on the AI-determined diagnosis and user location.

## 🛠️ Tech Stack

* **Backend & Frontend:** Python, Flask (Server-Side Rendering)
* **Database:** MySQL
* **AI Integration:** Google Gemini API
* **Data Handling:** Pandas, MySQL Connector
* **Tools:** Git, Postman (for API testing)

## ⚙️ Prerequisites

Before running the project, ensure you have the following installed:
* [Python](https://www.python.org/) (v3.8+)
* [MySQL Server](https://dev.mysql.com/downloads/mysql/)

## 📦 Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/zaidmohammed7/Medibuddy.git](https://github.com/zaidmohammed7/Medibuddy.git)
cd medibuddy
```

### 2. Database Setup 🗄️
*You must set up the database structure and populate it with data before running the app.*

1.  **Create the Database:**
    Open your MySQL client (Workbench or Command Line) and create a new database (e.g., `aloo`).

2.  **Populate the Data:**
    Locate the `aloo-dump` folder in the root directory. Run the SQL files in the order shown below:

    *Command Line Example:*
    ```bash
    # Run the main dump first
    mysql -u root -p aloo < aloo-dump/aloo-dump.sql

    # Run the supplementary tables
    mysql -u root -p aloo < aloo-dump/aloo-other-tables.sql

    # Run any triggers or stored procedures
    mysql -u root -p aloo < aloo-dump/refill_trigger.sql
    mysql -u root -p aloo < aloo-dump/stored_procedure.sql
    ```

### 3. Python Setup
Navigate to the project root and set up your virtual environment.

```bash
# Create virtual environment
python -m venv venv

# Activate Virtual Env:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. 🤖 Train the AI Model (Critical Step)
*This repository does not contain the pre-trained model files (`.pkl`) because they are large. You must generate them locally.*

1.  **Update DB Credentials for Training:**
    Open `train_model.py` and update the `MYSQL_CONFIG` dictionary with your MySQL password.

2.  **Run the Training Script:**
    This will fetch data from your SQL database, generate synthetic patients, and train the Random Forest model.
    ```bash
    python train_model.py
    ```
    *Success Message:* `Done! You now have an AI model.` (You should see `model_forest.pkl` and `model_encoder.pkl` appear in your folder).

### 5. Configuration ⚙️
You need to manually connect the application to your local database and API keys.

1.  **API Keys:**
    Ensure you have a file at `config/api.env` containing your Gemini API key:
    ```env
    GEMINI_API_KEY=your_actual_api_key_here
    FLASK_SECRET_KEY=your_secret_key
    ```

2.  **Update Database Credentials:**
    You must update the database connection strings in **two files** to match your local MySQL username and password.

    * **File 1: `app.py`** (Look for the `get_db()` function):
        ```python
        conn = mysql.connector.connect(
            host="localhost",
            user="root",          # Change to your MySQL username
            password="your_password", # Change to your MySQL password
            database="aloo"       # Ensure this matches your DB name
        )
        ```

    * **File 2: `chatbot.py`** (Look for the `MYSQL_CONFIG` dictionary at the top):
        ```python
        MYSQL_CONFIG = {
            "host": "localhost",
            "user": "root",
            "password": "your_password", # Update this
            "database": "aloo",
        }
        ```

## 🏃‍♂️ Usage

1.  **Activate your virtual environment** (if not already active).

2.  **Run the Flask Application:**
    ```bash
    python app.py
    ```

3.  **Access the App:**
    Open your web browser and go to: `http://127.0.0.1:5000`

## 🛡️ License

This project is open-source and available under the [MIT License](LICENSE).
