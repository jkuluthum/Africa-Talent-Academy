from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

app = FastAPI()

# Allow CORS for local development (adjust origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shared_data")
CSV_PATH = os.path.join(DATA_DIR, "savings.csv")

def calculate_final_grade(row):
    # Example: weights for courseworks, test, final
    weights = {
        'coursework': 0.4,
        'test': 0.3,
        'final': 0.3
    }
    # Calculate weighted sum
    total = (row['coursework'] * weights['coursework'] +
             row['test'] * weights['test'] +
             row['final'] * weights['final'])
    return round(total, 2)

@app.post("/upload-grades/")
async def upload_grades(file: UploadFile = File(...)):
    # Save uploaded CSV to shared_data
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    contents = await file.read()
    with open(CSV_PATH, "wb") as f:
        f.write(contents)

    # Read CSV with pandas
    df = pd.read_csv(CSV_PATH)

    # Check required columns
    required_cols = {'student_name', 'coursework', 'test', 'final'}
    if not required_cols.issubset(df.columns):
        return {"error": f"CSV must contain columns: {required_cols}"}

    # Calculate final grade
    df['final_grade'] = df.apply(calculate_final_grade, axis=1)

    # Save updated CSV with final grades
    df.to_csv(CSV_PATH, index=False)

    # Return results as JSON
    results = df[['student_name', 'final_grade']].to_dict(orient='records')
    return {"results": results}

@app.get("/grades/")
def get_grades():
    # Return grades from CSV if exists
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        return {"results": df[['student_name', 'final_grade']].to_dict(orient='records')}
    else:
        return {"results": []}
    

@app.get("/download-csv/")
def download_csv():
    if os.path.exists(CSV_PATH):
        return FileResponse(CSV_PATH, filename="final_grades.csv", media_type='text/csv')
    return {"error": "No CSV file found."}
