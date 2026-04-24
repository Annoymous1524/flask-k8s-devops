from flask import Flask
import mysql.connector
import os

app = Flask(__name__)

@app.route('/')
def home():
    try:
        db = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return "Hello DevOps CI/CD 🚀"
    except Exception as e:
        return f"DB Connection Failed ❌: {e}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
