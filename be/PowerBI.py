from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import contextmanager
import pyodbc
import requests
import json
from fastapi import FastAPI, Request, Header, HTTPException,Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import json
import pandas as pd
import tempfile
import os
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ SQL Server DB Config
db_config = {
    'server': '111.93.26.122',
    'database': 'Oliva',
    'username': 'sa',
    'password': 'Oliva@9876'
}

# ✅ Build ODBC connection string
connection_string = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={db_config['server']};"
    f"DATABASE={db_config['database']};"
    f"UID={db_config['username']};"
    f"PWD={db_config['password']}"
)

# ✅ Context manager for DB connection
@contextmanager
def get_db_connection():
    conn = pyodbc.connect(connection_string)
    try:
        yield conn
    finally:
        conn.close()

# ✅ Create new tables if they don't exist
def create_tables():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create new users table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'powerbi_users_new')
                BEGIN
                    CREATE TABLE dbo.powerbi_users_new (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        username VARCHAR(100) UNIQUE,
                        password VARCHAR(100),
                        role VARCHAR(50)
                    )
                END
            """)
            
            # Create new reports table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'powerbi_reports_new')
                BEGIN
                    CREATE TABLE dbo.powerbi_reports_new (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        username VARCHAR(100),
                        dashboard_name VARCHAR(200),
                        group_id VARCHAR(100),
                        report_id VARCHAR(100)
                    )
                END
            """)
            
            # Create page permissions table with page_id instead of page_name
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'powerbi_page_permissions')
                BEGIN
                    CREATE TABLE dbo.powerbi_page_permissions (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        username VARCHAR(100),
                        report_id VARCHAR(100),
                        page_id VARCHAR(100),
                        created_at DATETIME DEFAULT GETDATE(),
                        CONSTRAINT UC_PagePermission UNIQUE (username, report_id, page_id)
                    )
                END
            """)

            # Create user filters table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'powerbi_user_filters')
                BEGIN
                    CREATE TABLE dbo.powerbi_user_filters (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        username VARCHAR(100),
                        report_id VARCHAR(100),
                        table_name VARCHAR(100),
                        column_name VARCHAR(100),
                        filter_values TEXT,
                        filter_type VARCHAR(50),
                        operator VARCHAR(20),
                        created_at DATETIME DEFAULT GETDATE(),
                        updated_at DATETIME DEFAULT GETDATE(),
                        CONSTRAINT UC_UserFilter UNIQUE (username, report_id, table_name, column_name)
                    )
                END
            """)
            
            conn.commit()
    except Exception as e:
        print(f"Error creating tables: {str(e)}")

# Call create_tables when app starts
create_tables()

# ✅ Login Request/Response Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    message: str
    user: dict

@app.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Use only new users table
            cursor.execute("""
                SELECT id, username, role 
                FROM dbo.powerbi_users_new
                WHERE username = ? AND password = ?
            """, request.username, request.password)
            user = cursor.fetchone()
            if user:
                return {"message": "Login successful", "user": {"username": user.username, "role": user.role}}
            else:
                raise HTTPException(status_code=401, detail="Invalid username or password")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ✅ Report List Endpoint
@app.get("/get-reports")
async def get_reports(username: str = Query(...)):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get user's role from new users table
            cursor.execute("""
                SELECT role 
                FROM dbo.powerbi_users_new
                WHERE username = ?
            """, username)
            user_role = cursor.fetchone()
            
            if not user_role:
                raise HTTPException(status_code=404, detail="User not found")
                
            # Get reports from new reports table with page IDs
            cursor.execute("""
                SELECT r.dashboard_name, r.group_id, r.report_id,
                       (
                           SELECT STRING_AGG(page_id, ',')
                           FROM dbo.powerbi_page_permissions pa
                           WHERE pa.username = ? 
                           AND pa.report_id = r.report_id
                       ) as allowed_pages
                FROM dbo.powerbi_reports_new r
                WHERE r.username = ?
            """, username, username)
            
            rows = cursor.fetchall()
            reports = []
            
            for row in rows:
                allowed_pages = []
                if row.allowed_pages:
                    allowed_pages = [page_id.strip() for page_id in row.allowed_pages.split(',') if page_id.strip()]
                
                reports.append({
                    "dashboard": row.dashboard_name,
                    "group_id": row.group_id,
                    "report_id": row.report_id,
                    "allowed_pages": allowed_pages if user_role.role != 'admin' else None
                })
                
            if not reports:
                raise HTTPException(status_code=404, detail="No reports found for this user.")
            return JSONResponse(content=reports)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Add endpoints to manage users and reports in new tables
class NewUserRequest(BaseModel):
    username: str
    password: str
    role: str

@app.post("/add-user")
async def add_user(request: NewUserRequest):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dbo.powerbi_users_new (username, password, role)
                VALUES (?, ?, ?)
            """, request.username, request.password, request.role)
            conn.commit()
            return {"message": "User added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

class NewReportRequest(BaseModel):
    username: str
    dashboard_name: str
    group_id: str
    report_id: str

@app.post("/add-report")
async def add_report(request: NewReportRequest):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dbo.powerbi_reports_new (username, dashboard_name, group_id, report_id)
                VALUES (?, ?, ?, ?)
            """, request.username, request.dashboard_name, request.group_id, request.report_id)
            conn.commit()
            return {"message": "Report added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Add new endpoint to manage page permissions with IDs
@app.post("/set-page-permissions")
async def set_page_permissions(username: str, report_id: str, page_ids: list[str]):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # First verify user exists
            cursor.execute("""
                SELECT username FROM dbo.powerbi_users_new 
                WHERE username = ?
            """, username)
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="User not found")
            
            # Verify report exists
            cursor.execute("""
                SELECT report_id FROM dbo.powerbi_reports_new 
                WHERE report_id = ?
            """, report_id)
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Report not found")
            
            # Delete existing permissions
            cursor.execute("""
                DELETE FROM dbo.powerbi_page_permissions 
                WHERE username = ? AND report_id = ?
            """, username, report_id)
            
            # Insert new permissions using page IDs
            for page_id in page_ids:
                cursor.execute("""
                    INSERT INTO dbo.powerbi_page_permissions (username, report_id, page_id)
                    VALUES (?, ?, ?)
                """, username, report_id, page_id)
            
            conn.commit()
            return {"message": "Page permissions updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.delete("/remove-page-permission")
async def remove_page_permission(username: str = Query(...), report_id: str = Query(...), page_name: str = Query(...)):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM dbo.powerbi_page_access 
                WHERE username = ? AND report_id = ? AND page_name = ?
            """, username, report_id, page_name)
            conn.commit()
            return {"message": "Page permission removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ✅ Power BI Token Endpoint
class PowerBIRequest(BaseModel):
    group_id: str
    report_id: str
    username: str  # Added username parameter

class PowerBIResponse(BaseModel):
    access_token: str

@app.post("/get-powerbi-tokens", response_model=PowerBIResponse)
async def get_powerbi_embed_token(payload: PowerBIRequest):
    client_id = '7a728f18-f512-4848-897a-2e0504c09780'
    client_secret = 'WkE8Q~6sUdpglGh65QQTgWSaCadCJJLnRhOAQaLd'
    tenant_id = 'e5a1ed1e-89cc-452d-8b50-88daaa995199'

    try:
        # First verify user has access to this report
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.report_id, u.role,
                       (
                           SELECT STRING_AGG(page_id, ',')
                           FROM dbo.powerbi_page_permissions pa
                           WHERE pa.username = ? 
                           AND pa.report_id = r.report_id
                       ) as allowed_pages
                FROM dbo.powerbi_reports_new r
                JOIN dbo.powerbi_users_new u ON r.username = u.username
                WHERE r.report_id = ? AND r.username = ?
            """, payload.username, payload.report_id, payload.username)
            
            report_access = cursor.fetchone()
            if not report_access and report_access.role != 'admin':
                raise HTTPException(status_code=403, detail="User does not have access to this report")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying report access: {str(e)}")

    # Step 1: Get Azure AD token
    try:
        token_response = requests.post(
            f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token',
            data={
                'client_id': client_id,
                'scope': 'https://analysis.windows.net/powerbi/api/.default',
                'client_secret': client_secret,
                'grant_type': 'client_credentials',
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=500, detail="Access token missing")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Azure token error: {str(e)}")

    # Step 2: Generate Power BI Embed Token
    try:
        generate_token_url = f"https://api.powerbi.com/v1.0/myorg/groups/{payload.group_id}/reports/{payload.report_id}/GenerateToken"

        # Special handling for one specific report
        if payload.report_id == "b46db7ca-a042-40d1-9458-012b5c889d80":
            embed_body = {
                "accessLevel": "View",
                "identities": [
                    {
                        "username": "devops@olivaclinic.com",
                        "roles": ["admin"],
                        "datasets": ["9dfe5e82-2f55-40c2-b8a5-8241ca9ab741"]
                    }
                ]
            }
        else:
            # Default body for other reports
            embed_body = {
                "accessLevel": "View"
            }

        embed_response = requests.post(
            generate_token_url,
            json=embed_body,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
        )
        embed_response.raise_for_status()
        return PowerBIResponse(access_token=embed_response.json()["token"])
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Power BI token generation error: {str(e)}")

@app.post("/webhook")
async def webhook_endpoint(request: Request):
    form = await request.form()
    form_dict = dict(form)

    # Prepare data
    booking_id = form_dict.get("booking_id")
    remarks = form_dict.get("remarks")
    wtype = form_dict.get("type")
    status = form_dict.get("status")

    phlebo_id = form_dict.get("phlebotomist[id]")
    phlebo_name = form_dict.get("phlebotomist[name]")
    phlebo_mobile = form_dict.get("phlebotomist[mobile_no]")
    phlebo_start_time = form_dict.get("phlebotomist[start_time]")
    phlebo_end_time = form_dict.get("phlebotomist[end_time]")
    phlebo_date = form_dict.get("phlebotomist[sample_collection_date]")
    report_url = form_dict.get("reportUrl[0]")

    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        # Check if the booking_id already exists
        cursor.execute("SELECT COUNT(*) FROM WebhookLogs WHERE booking_id = ?", booking_id)
        exists = cursor.fetchone()[0]

        if exists:
            # Update the existing record
            cursor.execute("""
                UPDATE WebhookLogs SET
                    remarks = ?, type = ?, status = ?,
                    phlebo_id = ?, phlebo_name = ?, phlebo_mobile = ?,
                    phlebo_start_time = ?, phlebo_end_time = ?,
                    phlebo_sample_collection_date = ?, report_url = ?
                WHERE booking_id = ?
            """, (
                remarks, wtype, status,
                phlebo_id, phlebo_name, phlebo_mobile,
                phlebo_start_time, phlebo_end_time,
                phlebo_date, report_url,
                booking_id
            ))
        else:
            # Insert a new record
            cursor.execute("""
                INSERT INTO WebhookLogs (
                    booking_id, remarks, type, status,
                    phlebo_id, phlebo_name, phlebo_mobile,
                    phlebo_start_time, phlebo_end_time,
                    phlebo_sample_collection_date, report_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                booking_id, remarks, wtype, status,
                phlebo_id, phlebo_name, phlebo_mobile,
                phlebo_start_time, phlebo_end_time,
                phlebo_date, report_url
            ))

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        # Logging can be added here if needed
        pass

    return {"message": "Webhook processed"}

# ✅ Run the app (for local testing)
# if __name__ == '__main__':
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8001)



# Add new models for filter management
class FilterRequest(BaseModel):
    username: str
    report_id: str
    table_name: str
    column_name: str
    filter_values: list[str]
    filter_type: str = "Include"  # Include or Exclude
    operator: str = "In"  # In, Equals, Contains, etc.

@app.post("/set-user-filter")
async def set_user_filter(request: FilterRequest):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Convert filter values list to comma-separated string
            filter_values_str = ','.join(request.filter_values)
            
            # Upsert the filter
            cursor.execute("""
                IF EXISTS (
                    SELECT 1 FROM dbo.powerbi_user_filters 
                    WHERE username = ? AND report_id = ? AND table_name = ? AND column_name = ?
                )
                BEGIN
                    UPDATE dbo.powerbi_user_filters
                    SET filter_values = ?,
                        filter_type = ?,
                        operator = ?,
                        updated_at = GETDATE()
                    WHERE username = ? 
                    AND report_id = ? 
                    AND table_name = ? 
                    AND column_name = ?
                END
                ELSE
                BEGIN
                    INSERT INTO dbo.powerbi_user_filters (
                        username, report_id, table_name, column_name, 
                        filter_values, filter_type, operator
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                END
            """, (
                request.username, request.report_id, request.table_name, request.column_name,
                filter_values_str, request.filter_type, request.operator,
                request.username, request.report_id, request.table_name, request.column_name,
                request.username, request.report_id, request.table_name, request.column_name,
                filter_values_str, request.filter_type, request.operator
            ))
            
            conn.commit()
            return {"message": "Filter updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/get-user-filters/{username}/{report_id}")
async def get_user_filters(username: str, report_id: str):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT table_name, column_name, filter_values, filter_type, operator
                FROM dbo.powerbi_user_filters
                WHERE username = ? AND report_id = ?
            """, username, report_id)
            
            rows = cursor.fetchall()
            filters = []
            
            for row in rows:
                filter_values = [v.strip() for v in row.filter_values.split(',') if v.strip()]
                filters.append({
                    "table_name": row.table_name,
                    "column_name": row.column_name,
                    "filter_values": filter_values,
                    "filter_type": row.filter_type,
                    "operator": row.operator
                })
            
            return {"filters": filters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.delete("/delete-user-filter")
async def delete_user_filter(username: str = Query(...), report_id: str = Query(...), 
                           table_name: str = Query(...), column_name: str = Query(...)):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM dbo.powerbi_user_filters 
                WHERE username = ? 
                AND report_id = ? 
                AND table_name = ? 
                AND column_name = ?
            """, username, report_id, table_name, column_name)
            conn.commit()
            return {"message": "Filter deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/export-report")
async def export_report(request: Request):
    body = await request.json()
    username = body.get("username")
    report_id = body.get("report_id")
    file_type = body.get("file_type", "csv")

    # 1. Check user permissions (reuse logic from get-reports)
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Check user role
            cursor.execute("""
                SELECT role FROM dbo.powerbi_users_new WHERE username = ?
            """, username)
            user_role = cursor.fetchone()
            if not user_role:
                raise HTTPException(status_code=404, detail="User not found")

            # Get allowed pages for this report (if not admin)
            allowed_pages = None
            if user_role.role != 'admin':
                cursor.execute("""
                    SELECT STRING_AGG(page_id, ',') as allowed_pages
                    FROM dbo.powerbi_page_permissions
                    WHERE username = ? AND report_id = ?
                """, username, report_id)
                row = cursor.fetchone()
                if row and row.allowed_pages:
                    allowed_pages = [p.strip() for p in row.allowed_pages.split(',') if p.strip()]

            # Get user filters
            cursor.execute("""
                SELECT table_name, column_name, filter_values, filter_type, operator
                FROM dbo.powerbi_user_filters
                WHERE username = ? AND report_id = ?
            """, username, report_id)
            filters = cursor.fetchall()

            # --- SAMPLE DATA QUERY ---
            # Replace this with your actual report data query logic
            # For now, just select all rows from a sample table (e.g., ReportData)
            query = "SELECT * FROM ReportData WHERE report_id = ?"
            params = [report_id]
            # Apply allowed pages filter if not admin
            if allowed_pages:
                query += " AND page_id IN (" + ",".join([f"'"+p+"'" for p in allowed_pages]) + ")"
            # You can also apply user filters here if needed
            cursor.execute(query, *params)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            data = [dict(zip(columns, row)) for row in rows]

            # Convert to DataFrame
            df = pd.DataFrame(data)
            # Optionally, apply further filtering in pandas if needed

            # Write to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
                df.to_csv(tmp.name, index=False)
                tmp_path = tmp.name

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

    # Return file as download
    response = FileResponse(tmp_path, filename=f"report_{report_id}.csv", media_type="text/csv")
    # Clean up temp file after sending
@app.post("/export-visual")
async def export_visual(request: Request):
    body = await request.json()
    group_id = body["group_id"]
    report_id = body["report_id"]
    page_name = body["page_name"]
    visual_name = body["visual_name"]
    export_format = body.get("format", "xlsx")
    username = body.get("username")  # Optional, for permission checks

    # 1. Get Power BI access token (reuse your logic)
    client_id = '7a728f18-f512-4848-897a-2e0504c09780'
    client_secret = 'WkE8Q~6sUdpglGh65QQTgWSaCadCJJLnRhOAQaLd'
    tenant_id = 'e5a1ed1e-89cc-452d-8b50-88daaa995199'
    try:
        token_response = requests.post(
            f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token',
            data={
                'client_id': client_id,
                'scope': 'https://analysis.windows.net/powerbi/api/.default',
                'client_secret': client_secret,
                'grant_type': 'client_credentials',
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=500, detail="Access token missing")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Azure token error: {str(e)}")

    # 2. Call the exportTo API
    export_url = f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/reports/{report_id}/pages/{page_name}/visuals/{visual_name}/exportTo"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    print(export_url)
    print(headers)
    export_body = {"format": export_format}
    export_response = requests.post(export_url, json=export_body, headers=headers)
    print(export_response)
    if export_response.status_code not in (202, 200):
        raise HTTPException(status_code=500, detail=f"ExportTo API failed: {export_response.text}")

    # 3. Poll for status
    export_location = export_response.headers.get("Location")
    if not export_location:
        raise HTTPException(status_code=500, detail="No export location returned")
    for _ in range(30):  # Poll for up to 30*2=60 seconds
        status_response = requests.get(export_location, headers=headers)
        status_response.raise_for_status()
        status_json = status_response.json()
        if status_json.get("status") == "Succeeded":
            resource_location = status_json.get("resourceLocation")
            break
        elif status_json.get("status") == "Failed":
            raise HTTPException(status_code=500, detail="Export failed")
        time.sleep(2)
    else:
        raise HTTPException(status_code=500, detail="Export timed out")

    # 4. Download the file
    file_response = requests.get(resource_location, headers=headers)
    if file_response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to download exported file")

    # 5. Return as FileResponse
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{export_format}') as tmp:
        tmp.write(file_response.content)
        tmp_path = tmp.name

    response = FileResponse(tmp_path, filename=f"visual_export.{export_format}", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("PowerBI:app", host="0.0.0.0", port=9000, reload=True)
