from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from supabase import create_client, Client
import os
from io import BytesIO

app = Flask(__name__)
app.secret_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzem5wYm9xdXR6eHB5d3Bzd3pqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUxNzIyNzksImV4cCI6MjA3MDc0ODI3OX0.GuWprRk5n0uoCww_WXHIt2cQJhi038oKd6WDxO__JK0"  # Change this in production

# Supabase configuration
SUPABASE_URL = "https://tsznpboqutzxpywpswzj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzem5wYm9xdXR6eHB5d3Bzd3pqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUxNzIyNzksImV4cCI6MjA3MDc0ODI3OX0.GuWprRk5n0uoCww_WXHIt2cQJhi038oKd6WDxO__JK0"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    bucket_name = request.args.get('bucket', 'my-files')
    folder_path = request.args.get('folder', '')
    
    try:
        list_options = {"limit": 100, "offset": 0}
        if folder_path:
            list_options["prefix"] = folder_path
        
        res = supabase.storage.from_(bucket_name).list(folder_path, list_options)
        
        contents = []
        if isinstance(res, list):
            data = res
        elif isinstance(res, dict) and 'data' in res:
            data = res['data']
        else:
            data = []
            
        for item in data:
            if not item or not isinstance(item, dict):
                continue

            name = item.get("name", "")
            if not name or name == folder_path:
                continue

            if item.get("metadata") is None:
                contents.append({
                    "name": name,
                    "type": "folder",
                    "path": name
                })
            else:
                contents.append({
                    "name": name,
                    "type": "file", 
                    "path": name,
                    "size": item.get("metadata", {}).get("size", 0)
                })
                
    except Exception as e:
        flash(f"Error fetching contents: {str(e)}")
        contents = []
    
    return render_template("index.html", 
                         contents=contents, 
                         bucket_name=bucket_name,
                         current_folder=folder_path)

@app.route('/upload/<bucket>', methods=['POST'])
def upload_file(bucket):
    file = request.files.get("file")
    folder = request.form.get("folder", "").strip()
    
    if not file or file.filename == '':
        flash("No file selected.")
        return redirect(url_for('index', bucket=bucket))
    
    try:
        file_path = f"{folder.rstrip('/')}/{file.filename}" if folder else file.filename
        file_content = file.read()
        res = supabase.storage.from_(bucket).upload(file_path, file_content)
        
        if isinstance(res, dict) and res.get("error"):
            flash(f"Upload error: {res['error']['message']}")
        else:
            flash(f"File '{file.filename}' uploaded successfully.")
            
    except Exception as e:
        flash(f"Upload error: {str(e)}")
    
    return redirect(url_for('index', bucket=bucket, folder=folder))

@app.route('/create_folder/<bucket>', methods=['POST'])
def create_folder(bucket):
    folder_name = request.form.get("folder_name", "").strip()
    parent_folder = request.form.get("parent_folder", "").strip()
    
    if not folder_name:
        flash("Folder name is required.")
        return redirect(url_for('index', bucket=bucket))
    
    try:
        folder_path = f"{parent_folder.rstrip('/')}/{folder_name}/" if parent_folder else f"{folder_name}/"
        res = supabase.storage.from_(bucket).upload(f"{folder_path}.keep", b'')
        
        if isinstance(res, dict) and res.get("error"):
            flash(f"Error creating folder: {res['error']['message']}")
        else:
            flash(f"Folder '{folder_name}' created successfully.")
            
    except Exception as e:
        flash(f"Error creating folder: {str(e)}")
    
    return redirect(url_for('index', bucket=bucket, folder=parent_folder))

@app.route('/delete_file/<bucket>')
def delete_file(bucket):
    file_path = request.args.get('path')
    folder = request.args.get('folder', '')
    
    if not file_path:
        flash("File path is required.")
        return redirect(url_for('index', bucket=bucket))
    
    try:
        res = supabase.storage.from_(bucket).remove([file_path])
        
        if isinstance(res, dict) and res.get("error"):
            flash(f"Error deleting file: {res['error']['message']}")
        else:
            flash(f"File '{file_path}' deleted successfully.")
            
    except Exception as e:
        flash(f"Error deleting file: {str(e)}")
    
    return redirect(url_for('index', bucket=bucket, folder=folder))

@app.route('/delete_folder/<bucket>')
def delete_folder(bucket):
    folder_path = request.args.get('path')
    parent_folder = request.args.get('parent', '')
    
    if not folder_path:
        flash("Folder path is required.")
        return redirect(url_for('index', bucket=bucket))
    
    try:
        res = supabase.storage.from_(bucket).list(folder_path, {"limit": 1000})
        files_to_delete = []

        if isinstance(res, list):
            for item in res:
                if not item or not isinstance(item, dict):
                    continue
                if item.get('name'):
                    files_to_delete.append(f"{folder_path}/{item['name']}")
        elif isinstance(res, dict) and res.get('data'):
            for item in res['data']:
                if not item or not isinstance(item, dict):
                    continue
                if item.get('name'):
                    files_to_delete.append(f"{folder_path}/{item['name']}")

        files_to_delete.append(f"{folder_path}/.keep")
        
        if files_to_delete:
            delete_res = supabase.storage.from_(bucket).remove(files_to_delete)
            if isinstance(delete_res, dict) and delete_res.get("error"):
                flash(f"Error deleting folder: {delete_res['error']['message']}")
            else:
                flash(f"Folder '{folder_path}' deleted successfully.")
        else:
            flash("Folder is empty or does not exist.")
            
    except Exception as e:
        flash(f"Error deleting folder: {str(e)}")
    
    return redirect(url_for('index', bucket=bucket, folder=parent_folder))

@app.route('/copy_file/<bucket>', methods=["GET", "POST"])
def copy_file(bucket):
    file_path = request.args.get('path')
    folder = request.args.get('folder', '')
    
    if request.method == "GET":
        return render_template("copy_move.html", 
                             action="Copy", 
                             file_path=file_path,
                             bucket=bucket,
                             folder=folder,
                             default_path=f"copy_of_{file_path}")
    
    new_path = request.form.get("new_path", "").strip()
    if not new_path:
        flash("New path is required.")
        return redirect(url_for('index', bucket=bucket, folder=folder))
    
    try:
        data = supabase.storage.from_(bucket).download(file_path)
        if isinstance(data, dict) and data.get("error"):
            flash(f"Error downloading file: {data['error']['message']}")
            return redirect(url_for('index', bucket=bucket, folder=folder))
        
        res = supabase.storage.from_(bucket).upload(new_path, data)
        if isinstance(res, dict) and res.get("error"):
            flash(f"Error copying file: {res['error']['message']}")
        else:
            flash(f"File copied to '{new_path}' successfully.")
            
    except Exception as e:
        flash(f"Error copying file: {str(e)}")
    
    return redirect(url_for('index', bucket=bucket, folder=folder))

@app.route('/move_file/<bucket>', methods=["GET", "POST"])
def move_file(bucket):
    file_path = request.args.get('path')
    folder = request.args.get('folder', '')
    
    if request.method == "GET":
        return render_template("copy_move.html", 
                             action="Move", 
                             file_path=file_path,
                             bucket=bucket,
                             folder=folder,
                             default_path=f"moved_{file_path}")
    
    new_path = request.form.get("new_path", "").strip()
    if not new_path:
        flash("New path is required.")
        return redirect(url_for('index', bucket=bucket, folder=folder))
    
    try:
        data = supabase.storage.from_(bucket).download(file_path)
        if isinstance(data, dict) and data.get("error"):
            flash(f"Error downloading file: {data['error']['message']}")
            return redirect(url_for('index', bucket=bucket, folder=folder))
        
        res_upload = supabase.storage.from_(bucket).upload(new_path, data)
        if isinstance(res_upload, dict) and res_upload.get("error"):
            flash(f"Error moving file (upload failed): {res_upload['error']['message']}")
            return redirect(url_for('index', bucket=bucket, folder=folder))
        
        res_delete = supabase.storage.from_(bucket).remove([file_path])
        if isinstance(res_delete, dict) and res_delete.get("error"):
            flash(f"File moved but failed to delete original: {res_delete['error']['message']}")
        else:
            flash(f"File moved to '{new_path}' successfully.")
            
    except Exception as e:
        flash(f"Error moving file: {str(e)}")
    
    return redirect(url_for('index', bucket=bucket, folder=folder))

@app.route('/download/<bucket>')
def download_file(bucket):
    file_path = request.args.get('path')
    
    if not file_path:
        flash("File path is required.")
        return redirect(url_for('index', bucket=bucket))
    
    try:
        res = supabase.storage.from_(bucket).create_signed_url(file_path, 3600)
        if isinstance(res, dict) and res.get("error"):
            flash(f"Error creating download link: {res['error']['message']}")
            return redirect(url_for('index', bucket=bucket))
        
        download_url = res.get("signedURL") if isinstance(res, dict) else None
        if download_url:
            return redirect(download_url)
        else:
            flash("Could not generate download link.")
            
    except Exception as e:
        flash(f"Error downloading file: {str(e)}")
    
    return redirect(url_for('index', bucket=bucket))

@app.route('/create_bucket', methods=["POST"])
def create_bucket():
    bucket_name = request.form.get("bucket_name", "").strip()
    if not bucket_name:
        flash("Bucket name is required.")
        return redirect(url_for('index'))
    
    flash("Bucket creation must be done via Supabase dashboard (requires admin access).")
    return redirect(url_for('index'))

@app.route('/list_buckets')
def list_buckets():
    try:
        flash("Bucket listing requires admin privileges. Use Supabase dashboard.")
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Error listing buckets: {str(e)}")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
