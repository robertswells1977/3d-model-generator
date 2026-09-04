import os
import time
import uuid
import psycopg2
import requests
from psycopg2.extras import RealDictCursor
from openai import OpenAI

DB_HOST = os.getenv("DB_HOST", "localhost")
LLM_URL = os.getenv("LLM_URL", "http://localhost:8080/v1")
FUSION_URL = os.getenv("FUSION_URL", "http://localhost:5000")
EXPORT_DIR_HOST = os.getenv("EXPORT_DIR_HOST", "/Users/robwells/sc/3d-model-generator/temp")

client = OpenAI(base_url=LLM_URL, api_key="sk-no-key-needed")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database="threed_generator",
        user="admin",
        password="password"
    )

def generate_fusion_script(description, attempt, previous_error=None):
    prompt = f"""
Write a complete, executable Python script for Autodesk Fusion 360 that builds the following item: {description}.
The script must import adsk.core and adsk.fusion.
It must create a new document, build the geometry, and EXPORT the final body as an STL file to EXACTLY this absolute path:
{EXPORT_DIR_HOST}/project_{{project_id}}_v{attempt}.stl

Do not include markdown blocks, just pure python code.
"""
    if previous_error:
        prompt += f"\n\nThe previous attempt failed with this error: {previous_error}\nPlease fix it."

    response = client.chat.completions.create(
        model="gemma-2-8b-it",
        messages=[
            {"role": "system", "content": "You are an expert Autodesk Fusion 360 API Python developer. Only output raw Python code. Do not wrap in markdown."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    code = response.choices[0].message.content.strip()
    if code.startswith("```python"):
        code = code[9:]
    if code.endswith("```"):
        code = code[:-3]
    return code.strip()

def process_project(project):
    project_id = project['id']
    description = project['description']
    
    print(f"Processing project {project_id}...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    previous_error = None
    
    for attempt in range(1, 11):
        print(f"Attempt {attempt} of 10...")
        try:
            # Generate code replacing placeholder with actual ID
            script = generate_fusion_script(description, attempt, previous_error)
            script = script.replace("{project_id}", str(project_id))
            
            # Send to Fusion
            print("Sending to Fusion 360...")
            resp = requests.post(f"{FUSION_URL}/run_script", json={"code": script}, timeout=60)
            
            if resp.status_code == 200:
                print("Fusion executed successfully!")
                # Insert version record
                version_id = str(uuid.uuid4())
                stl_path = f"/temp/project_{project_id}_v{attempt}.stl"
                
                cur.execute("""
                    INSERT INTO ProjectVersions (Id, ProjectId, VersionNumber, Status, FilePathSTL, AgentLog)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (version_id, project_id, attempt, "viable option", stl_path, "Success!"))
                conn.commit()
                
                # Mark project as completed
                cur.execute("UPDATE Projects SET Status = 'completed' WHERE Id = %s", (project_id,))
                conn.commit()
                break
            else:
                print(f"Fusion error: {resp.text}")
                previous_error = resp.text
                
        except Exception as e:
            print(f"Exception during attempt: {str(e)}")
            previous_error = str(e)
            
    else:
        # Failed 10 times
        print("Failed 10 attempts.")
        cur.execute("UPDATE Projects SET Status = 'failed' WHERE Id = %s", (project_id,))
        conn.commit()
        
    cur.close()
    conn.close()

def main_loop():
    print("Worker started. Polling for 'generating' projects...")
    while True:
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM Projects WHERE Status = 'generating' LIMIT 1")
            project = cur.fetchone()
            cur.close()
            conn.close()
            
            if project:
                process_project(project)
            else:
                time.sleep(5)
                
        except Exception as e:
            print(f"Database error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main_loop()
