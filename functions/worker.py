import os
import time
import uuid
import json
import psycopg2
import requests
from psycopg2.extras import RealDictCursor
from openai import OpenAI

DB_HOST = os.getenv("DB_HOST", "db")
LLM_URL = os.getenv("LLM_URL", "http://llama-server:8080/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma-2-2b-it")
FUSION_URL = os.getenv("FUSION_URL", "http://host.docker.internal:5000")
EXPORT_DIR_HOST = os.getenv("EXPORT_DIR_HOST", "/Users/robwells/sc/3d-model-generator/temp")
API_INTERNAL_URL = "http://api:5045/api"

client = OpenAI(base_url=LLM_URL, api_key="sk-no-key-needed")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database="threed_generator",
        user="admin",
        password="password"
    )

def log_to_project(project_id, msg):
    print(f"[{project_id}] {msg}")
    try:
        requests.post(f"{API_INTERNAL_URL}/projects/{project_id}/log", json={"message": msg}, timeout=5)
    except Exception as e:
        print(f"Failed to push log: {e}")

def process_planning(project):
    project_id = project['id']
    description = project['description']
    log_to_project(project_id, "Worker starting AI Approval plan generation...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        prompt = f"""
You are an expert CAD planner.
Analyze this description: "{description}"

Determine the structural components needed to build this model.
You must define AT LEAST ONE part in the "parts" array, even if it is a "single" model type.
For each part, provide an estimated height, width, and length (floats in cm).
Also provide a list of basic geometric shapes that could be used to construct the part (e.g. box, cylinder, sphere, polygon).
CRITICAL: If a part is a hole or a hollowed-out section, you MUST state "boolean cut" in the "connections" description. Do NOT just say "attached".

Return a JSON object matching this schema:
{{
  "type": "single" | "multi-part",
  "parts": [
    {{
      "name": "Base Shape",
      "height": 10.0,
      "width": 10.0,
      "length": 10.0,
      "shapes": ["cube", "sphere", etc],
      "connections": ["attached to top"]
    }}
  ],
  "image_prompt": "A clean 3D render of a..."
}}
"""
        log_to_project(project_id, f"Prompting LLM ({LLM_MODEL}) to structure CAD parts...")
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You output strict JSON. No markdown."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        
        plan_data = json.loads(content)
        log_to_project(project_id, "Successfully parsed CAD layout plan from LLM.")
        
        image_prompt = plan_data.get("image_prompt", f"3d model of {description}")
        sd_url = "https://sd.alreadyagents.com/sdapi/v1/txt2img"
        img_filename = f"plan_{project_id}.png"
        img_path = f"/temp/{img_filename}"
        
        log_to_project(project_id, f"Sending direct API call to Stable Diffusion for concept art (Prompt: {image_prompt})...")
        try:
            sd_resp = requests.post(sd_url, json={
                "prompt": image_prompt + ", high quality, 3d render, white background",
                "steps": 20,
                "width": 512,
                "height": 512
            }, timeout=30)
            if sd_resp.status_code == 200:
                import base64
                img_data = sd_resp.json()['images'][0]
                with open(img_path, "wb") as fh:
                    fh.write(base64.b64decode(img_data))
                plan_data['image_url'] = f"/temp/{img_filename}"
                log_to_project(project_id, "Stable Diffusion image received and saved.")
            else:
                plan_data['image_url'] = None
                log_to_project(project_id, f"Stable Diffusion API error: HTTP {sd_resp.status_code}")
        except Exception as e:
            log_to_project(project_id, f"SD API connection error: {e}")
            plan_data['image_url'] = None
            
        cur.execute("UPDATE Projects SET LLMPlan = %s, Status = 'planned' WHERE Id = %s", (json.dumps(plan_data), project_id))
        conn.commit()
        log_to_project(project_id, "Plan ready for User Approval!")
    except Exception as e:
        log_to_project(project_id, f"Planning error: {e}")
        fallback_plan = {"error": str(e), "raw": content if 'content' in locals() else ""}
        cur.execute("UPDATE Projects SET LLMPlan = %s, Status = 'planned' WHERE Id = %s", (json.dumps(fallback_plan), project_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()

def run_agent_loop(project_id, description, plan_json, stl_host_path, png_host_path):
    log_to_project(project_id, "Executing: Starting a fresh Fusion Workspace (new_design)...")
    try:
        requests.post(f"{FUSION_URL}/new_design", json={}, timeout=10)
    except:
        pass
        
    kb_path = os.path.join(os.path.dirname(__file__), "CAD_KNOWLEDGE_BASE.txt")
    cad_knowledge = ""
    if os.path.exists(kb_path):
        with open(kb_path, "r") as f:
            cad_knowledge = f.read()
            
    system_prompt = f"""
You are an autonomous AI CAD Engineer. You are building a 3D model in Autodesk Fusion 360.
You will think step-by-step and execute one tool at a time.

Fusion 360 Units: 1 unit = 1 cm = 10 mm. All mm dimensions must be divided by 10 (e.g. 10.0 becomes 1.0).

Available primitives:
1. "draw_box" - args: {{"width": float, "height": float, "depth": float, "x": float, "y": float, "z": float, "plane": "XY" | "XZ" | "YZ"}} (x, y is the CENTER)
2. "draw_cylinder" - args: {{"radius": float, "height": float, "x": float, "y": float, "z": float, "plane": "XY" | "XZ" | "YZ"}} (x, y is the CENTER)
3. "sphere" - args: {{"radius": float, "x": float, "y": float, "z": float}} (x, y, z is the CENTER)
4. "draw_lines" - args: {{"points": [[x,y,z], [x,y,z], ...]}} (Draws a closed 2D polygon)
5. "extrude_last_sketch" - args: {{"value": float, "taperangle": float}} (Extrudes the polygon you just drew)
6. "finish" - args: {{}} (Call this when the 3D model is completely finished)

{cad_knowledge}

To execute a tool (whether primitive or advanced), output a SINGLE JSON object (and NO OTHER TEXT) matching this format exactly:
{{"thought": "1. Analyze requirement: Need 4 legs for a table of height 5.\\n2. Calculate coords using trig at radius R=2.0: Leg 1=(2.0, 0), Leg 2=(0, 2.0), Leg 3=(-2.0, 0), Leg 4=(0, -2.0).\\n3. Set Z-axis to 0.", "tool": "draw_cylinder", "args": {{"radius": 0.3, "height": 5.0, "x": 2.0, "y": 0, "z": 0, "plane": "XY"}}}}

CRITICAL RULES:
1. You MUST write out your exact mathematical coordinate calculations inside the "thought" field before providing the "args". Do not guess coordinates.
2. You MUST output EXACTLY ONE tool call per response. NEVER stack multiple JSON objects. Execute one step, wait for the result, then execute the next.
3. Verify your "tool" selection matches your thought. Do NOT use "draw_box" when you mean to use "sphere" or "draw_cylinder". If you want a hole, you MUST use "boolean_operation" with "cut".

The system will then respond with the result of the tool execution. Then you will output the next tool call, until you call "finish".
"""
    clean_plan = {}
    try:
        clean_plan = json.loads(plan_json)
        if "image_url" in clean_plan:
            del clean_plan["image_url"]
    except:
        clean_plan = plan_json
        
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Build this project.\nDescription: {description}\nApproved Plan: {json.dumps(clean_plan)}"}
    ]
    
    endpoint_map = {
        "draw_box": "/Box",
        "draw_cylinder": "/draw_cylinder",
        "sphere": "/sphere",
        "draw_lines": "/draw_lines",
        "extrude_last_sketch": "/extrude_last_sketch",
        "fillet_edges": "/fillet_edges",
        "shell_body": "/shell_body",
        "revolve": "/revolve",
        "loft": "/loft",
        "holes": "/holes",
        "threaded": "/threaded",
        "cut_extrude": "/cut_extrude",
        "boolean_operation": "/boolean_operation",
        "arc": "/arc",
        "circular_pattern": "/circular_pattern",
        "rectangular_pattern": "/rectangular_pattern",
        "move_body": "/move_body"
    }
    
    max_steps = 15
    for step in range(max_steps):
        log_to_project(project_id, f"Agent Thinking (Step {step+1}/{max_steps})...")
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content.strip()
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            content = content[start_idx:end_idx+1]
        
        try:
            command = json.loads(content)
            thought = command.get("thought", "No thought provided")
            tool = command.get("tool")
            args = command.get("args", {})
            
            log_to_project(project_id, f"Agent Thought: {thought}")
            
            if tool == "finish":
                log_to_project(project_id, "Agent decided model is finished.")
                break
                
            path = endpoint_map.get(tool)
            if not path:
                error_msg = f"Unknown tool '{tool}'. Available tools: {list(endpoint_map.keys())} or 'finish'."
                log_to_project(project_id, f"Agent Tool Error: {error_msg}")
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": f"System Error: {error_msg}"})
                continue
                
            log_to_project(project_id, f"Executing Tool: {tool} -> {json.dumps(args)}")
            resp = requests.post(f"{FUSION_URL}{path}", json=args, timeout=30)
            
            if resp.status_code == 200:
                result_msg = "Success"
            else:
                result_msg = f"Fusion Error: {resp.text}"
                log_to_project(project_id, f"Tool failed: {result_msg}")
                
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": f"Tool Execution Result: {result_msg}"})
            
        except Exception as e:
            log_to_project(project_id, f"Agent generated invalid JSON: {content} (Error: {e})")
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": "System Error: Output was not valid JSON. You MUST output ONLY a JSON object."})

    # Finally, export STL
    try:
        log_to_project(project_id, f"Exporting final STL -> {stl_host_path}")
        export_args = {"Name": stl_host_path}
        resp = requests.post(f"{FUSION_URL}/Export_STL", json=export_args, timeout=30)
        if resp.status_code != 200:
            log_to_project(project_id, f"STL Export failed: {resp.text}")
            return False, resp.text
            
        # Capture Image
        log_to_project(project_id, f"Capturing render image -> {png_host_path}")
        img_args = {"Name": png_host_path}
        img_resp = requests.post(f"{FUSION_URL}/capture_image", json=img_args, timeout=30)
        if img_resp.status_code != 200:
            log_to_project(project_id, f"Warning: Failed to capture image: {img_resp.text}")
    except Exception as e:
        log_to_project(project_id, f"STL Export / Image Capture connection error: {e}")
        return False, str(e)
        
    return True, "Success"

def process_project(project):
    project_id = project['id']
    description = project['description']
    plan_json = project.get('llmplan', '{}')
    
    log_to_project(project_id, "Worker starting Agentic Generation phase...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    for attempt in range(1, 4):
        log_to_project(project_id, f"--- Generation Attempt {attempt}/3 ---")
        
        stl_filename = f"project_{project_id}_v{attempt}.stl"
        stl_host_path = f"{EXPORT_DIR_HOST}/{stl_filename}"
        stl_container_path = f"/temp/{stl_filename}"
        
        png_filename = f"project_{project_id}_v{attempt}.png"
        png_host_path = f"{EXPORT_DIR_HOST}/{png_filename}"
        png_container_path = f"/temp/{png_filename}"
        
        success, error_msg = run_agent_loop(project_id, description, plan_json, stl_host_path, png_host_path)
        
        if success:
            time.sleep(2)
            if os.path.exists(stl_container_path):
                log_to_project(project_id, "Fusion executed successfully and STL verified on disk!")
                
                # Check if PNG exists, fallback to None
                image_path_db = png_container_path if os.path.exists(png_container_path) else None
                
                version_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO ProjectVersions (Id, ProjectId, VersionNumber, Status, FilePathSTL, ImagePath, AgentLog)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (version_id, project_id, attempt, "viable option", f"/temp/{stl_filename}", image_path_db, "Success! Agent loop completed."))
                conn.commit()
                
                cur.execute("UPDATE Projects SET Status = 'completed' WHERE Id = %s", (project_id,))
                conn.commit()
                log_to_project(project_id, "Project generation entirely complete!")
                break
            else:
                log_to_project(project_id, "ERROR: Fusion returned 200, but STL file was NOT created on disk.")
                
        else:
            log_to_project(project_id, f"Agent Loop Failed: {error_msg}")
            
    else:
        log_to_project(project_id, "Failed 3 attempts. Project marked as failed.")
        cur.execute("UPDATE Projects SET Status = 'failed' WHERE Id = %s", (project_id,))
        conn.commit()
        
    cur.close()
    conn.close()

def main_loop():
    print("Worker started. Polling for 'planning' and 'generating' projects...")
    while True:
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("SELECT * FROM Projects WHERE Status = 'planning' LIMIT 1")
            project_to_plan = cur.fetchone()
            
            if project_to_plan:
                process_planning(project_to_plan)
                cur.close()
                conn.close()
                continue
                
            cur.execute("SELECT * FROM Projects WHERE Status = 'generating' LIMIT 1")
            project_to_generate = cur.fetchone()
            
            if project_to_generate:
                process_project(project_to_generate)
                cur.close()
                conn.close()
                continue
            
            cur.close()
            conn.close()
            time.sleep(2)
                
        except Exception as e:
            print(f"Database error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main_loop()
