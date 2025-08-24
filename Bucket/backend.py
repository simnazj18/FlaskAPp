from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from supabase import create_client, Client
import os
from io import BytesIO

app = Flask(__name__)
app.secret_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzem5wYm9xdXR6eHB5d3Bzd3pqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUxNzIyNzksImV4cCI6MjA3MDc0ODI3OX0.GuWprRk5n0uoCww_WXHIt2cQJhi038oKd6WDxO__JK0"

SUPABASE_URL = "https://tsznpboqutzxpywpswzj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzem5wYm9xdXR6eHB5d3Bzd3pqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTE3MjI3OSwiZXhwIjoyMDcwNzQ4Mjc5fQ.4ahSdkVP9-EticbF-agua0TESEbiD0sL6dkUM4Uuu7g"
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

            full_path = f"{folder_path.rstrip('/')}/{name}" if folder_path else name

            if item.get("metadata") is None:
                contents.append({
                    "name": name,
                    "type": "folder",
                    "path": full_path
                })
            else:
                contents.append({
                    "name": name,
                    "type": "file",
                    "path": full_path,
                    "size": item.get("metadata", {}).get("size", 0)
                })

    except Exception as e:
        flash(f"Error fetching contents: {str(e)}")
        contents = []

    
    available_buckets = get_available_buckets()

    return render_template("index.html",
                           contents=contents,
                           bucket_name=bucket_name,
                           current_folder=folder_path,
                           available_buckets=available_buckets)


def get_available_buckets():
    """Helper function to get list of available buckets"""
    try:
        print("[DEBUG] Fetching available buckets...")
        buckets_res = supabase.storage.list_buckets()
        print(f"[DEBUG] Raw buckets response type: {type(buckets_res)}")
        
        available_buckets = []

        
        if isinstance(buckets_res, list):
            print(f"[DEBUG] Response is a list with {len(buckets_res)} items")
            for i, bucket in enumerate(buckets_res):
                print(f"[DEBUG] Processing bucket {i}: {bucket}")
                print(f"[DEBUG] Bucket type: {type(bucket)}")
                
                if bucket:
                    try:
                        
                        if hasattr(bucket, 'name'):
                            bucket_name = bucket.name
                            print(f"[DEBUG] Found bucket.name: '{bucket_name}'")
                        elif hasattr(bucket, 'id'):
                            bucket_name = bucket.id
                            print(f"[DEBUG] Found bucket.id: '{bucket_name}'")
                        elif isinstance(bucket, dict):
                            
                            bucket_name = bucket.get('name', '')
                            print(f"[DEBUG] Found dict bucket name: '{bucket_name}'")
                        else:
                            
                            if hasattr(bucket, '__dict__'):
                                bucket_dict = bucket.__dict__
                                bucket_name = bucket_dict.get('name', bucket_dict.get('id', ''))
                                print(f"[DEBUG] Found bucket name from __dict__: '{bucket_name}'")
                            else:
                                bucket_name = str(bucket)
                                print(f"[DEBUG] Using string representation: '{bucket_name}'")
                        
                        print(f"[DEBUG] Raw bucket_name: '{bucket_name}' (type: {type(bucket_name)})")
                        
                        if bucket_name and bucket_name.strip():
                            stripped_name = bucket_name.strip()
                            available_buckets.append(stripped_name)
                            print(f"[DEBUG] Successfully added bucket: {stripped_name}")
                        else:
                            print(f"[DEBUG] Bucket name is empty or invalid")
                            
                    except Exception as e:
                        print(f"[DEBUG] Error processing bucket {i}: {str(e)}")
                        
                        try:
                            bucket_str = str(bucket)
                            print(f"[DEBUG] Bucket string repr: {bucket_str}")
                        except:
                            print(f"[DEBUG] Could not get string representation of bucket")
                else:
                    print(f"[DEBUG] Bucket is None")
        
        
        elif isinstance(buckets_res, dict):
            print(f"[DEBUG] Response is dict with keys: {list(buckets_res.keys())}")
            
            for key in ['buckets', 'data', 'items']:
                bucket_list = buckets_res.get(key, [])
                if isinstance(bucket_list, list):
                    for bucket in bucket_list:
                        if bucket and isinstance(bucket, dict):
                            bucket_name = bucket.get('name', '')
                            if bucket_name and bucket_name.strip():
                                available_buckets.append(bucket_name.strip())
                                print(f"[DEBUG] Added bucket: {bucket_name}")
                    break
        
        
        available_buckets = list(dict.fromkeys(available_buckets))
        
        
        if not available_buckets:
            print("[DEBUG] No buckets found, using default")
            available_buckets = ['my-files']
        
        print(f"[DEBUG] Final available buckets: {available_buckets}")
        return available_buckets

    except Exception as e:
        print(f"[DEBUG] Exception in get_available_buckets: {str(e)}")
        import traceback
        traceback.print_exc()
        return ['my-files']


@app.route('/debug_template')
def debug_template():
    bucket_name = request.args.get('bucket', 'my-files')
    folder_path = request.args.get('folder', '')
    
    available_buckets = get_available_buckets()
    
    return {
        "bucket_name": bucket_name,
        "current_folder": folder_path,
        "available_buckets": available_buckets,
        "available_buckets_type": str(type(available_buckets)),
        "available_buckets_length": len(available_buckets) if available_buckets else 0
    }


@app.route('/debug_buckets')
def debug_buckets():
    try:
        buckets_res = supabase.storage.list_buckets()
        return {
            "response_type": str(type(buckets_res)),
            "response_data": buckets_res,
            "keys": list(buckets_res.keys()) if isinstance(buckets_res, dict) else "Not a dict"
        }
    except Exception as e:
        return {"error": str(e)}


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


def delete_folder_recursive(bucket, folder_path):
    try:
        res = supabase.storage.from_(bucket).list(folder_path, {"limit": 1000})
        files_to_delete = []

        if isinstance(res, list):
            data = res
        elif isinstance(res, dict) and res.get('data'):
            data = res['data']
        else:
            data = []

        for item in data:
            if not item or not isinstance(item, dict):
                continue

            name = item.get('name')
            if not name:
                continue

            item_path = f"{folder_path.rstrip('/')}/{name}"

            if item.get('metadata') is None:
                delete_folder_recursive(bucket, item_path)
            else:
                files_to_delete.append(item_path)

        if files_to_delete:
            supabase.storage.from_(bucket).remove(files_to_delete)

        try:
            supabase.storage.from_(bucket).remove([f"{folder_path.rstrip('/')}/.keep"])
        except:
            pass

        return True

    except Exception as e:
        print(f"Error in recursive delete: {str(e)}")
        return False


@app.route('/delete_folder/<bucket>')
def delete_folder(bucket):
    folder_path = request.args.get('path')
    parent_folder = request.args.get('parent', '')

    if not folder_path:
        flash("Folder path is required.")
        return redirect(url_for('index', bucket=bucket))

    try:
        success = delete_folder_recursive(bucket, folder_path)

        if success:
            flash(f"Folder '{folder_path}' and all its contents deleted successfully.")
        else:
            flash(f"Error deleting folder '{folder_path}'. Some files may remain.")

    except Exception as e:
        flash(f"Error deleting folder: {str(e)}")

    return redirect(url_for('index', bucket=bucket, folder=parent_folder))


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


@app.route('/copy_file/<bucket>')
def copy_file(bucket):
    file_path = request.args.get('path')
    folder = request.args.get('folder', '')

    if not file_path:
        flash("File path is required.")
        return redirect(url_for('index', bucket=bucket))

    
    filename = file_path.split('/')[-1]
    default_path = f"{folder.rstrip('/')}/copy_of_{filename}" if folder else f"copy_of_{filename}"

    return render_template("copy_move.html", 
                         action="Copy",
                         file_path=file_path,
                         default_path=default_path,
                         bucket=bucket,
                         folder=folder)


@app.route('/copy_file/<bucket>', methods=['POST'])
def copy_file_post(bucket):
    file_path = request.args.get('path')
    folder = request.args.get('folder', '')
    new_path = request.form.get('new_path', '').strip()

    if not file_path or not new_path:
        flash("File path and new path are required.")
        return redirect(url_for('index', bucket=bucket, folder=folder))

    try:
        
        res = supabase.storage.from_(bucket).download(file_path)
        
        if isinstance(res, dict) and res.get("error"):
            flash(f"Error copying file: {res['error']['message']}")
            return redirect(url_for('index', bucket=bucket, folder=folder))

        
        upload_res = supabase.storage.from_(bucket).upload(new_path, res)
        
        if isinstance(upload_res, dict) and upload_res.get("error"):
            flash(f"Error copying file: {upload_res['error']['message']}")
        else:
            flash(f"File copied successfully to '{new_path}'.")

    except Exception as e:
        flash(f"Error copying file: {str(e)}")

    return redirect(url_for('index', bucket=bucket, folder=folder))


@app.route('/move_file/<bucket>')
def move_file(bucket):
    file_path = request.args.get('path')
    folder = request.args.get('folder', '')

    if not file_path:
        flash("File path is required.")
        return redirect(url_for('index', bucket=bucket))

    
    filename = file_path.split('/')[-1]
    default_path = f"{folder.rstrip('/')}/{filename}" if folder else filename

    return render_template("copy_move.html", 
                         action="Move",
                         file_path=file_path,
                         default_path=default_path,
                         bucket=bucket,
                         folder=folder)


@app.route('/move_file/<bucket>', methods=['POST'])
def move_file_post(bucket):
    file_path = request.args.get('path')
    folder = request.args.get('folder', '')
    new_path = request.form.get('new_path', '').strip()

    if not file_path or not new_path:
        flash("File path and new path are required.")
        return redirect(url_for('index', bucket=bucket, folder=folder))

    try:
        
        res = supabase.storage.from_(bucket).move(file_path, new_path)
        
        if isinstance(res, dict) and res.get("error"):
            flash(f"Error moving file: {res['error']['message']}")
        else:
            flash(f"File moved successfully to '{new_path}'.")

    except Exception as e:
        flash(f"Error moving file: {str(e)}")

    return redirect(url_for('index', bucket=bucket, folder=folder))


@app.route('/create_bucket', methods=["POST"])
def create_bucket():
    bucket_name = request.form.get("bucket_name", "").strip()
    bucket_public = request.form.get("bucket_public") == "on"

    if not bucket_name:
        flash("Bucket name is required.")
        return redirect(url_for('index'))

    try:
        print(f"[DEBUG] Creating bucket: {bucket_name}, public: {bucket_public}")
        res = supabase.storage.create_bucket(bucket_name, options={"public": bucket_public})
        print(f"[DEBUG] Create bucket response: {res}")

        if isinstance(res, dict):
            if res.get("error"):
                raise Exception(res['error'].get('message', str(res['error'])))
            elif res.get("statusCode") and res["statusCode"] >= 400:
                raise Exception(res.get('message', 'Unknown error'))
            else:
                flash(f"Bucket '{bucket_name}' created successfully.")
                return redirect(url_for('index', bucket=bucket_name))
        else:
            flash(f"Bucket '{bucket_name}' created successfully.")
            return redirect(url_for('index', bucket=bucket_name))

    except Exception as e:
        flash(f"Error creating bucket: {str(e)}")
        return redirect(url_for('index'))


@app.route('/delete_bucket', methods=["POST"])
def delete_bucket():
    bucket_name = request.form.get("bucket_name", "").strip()

    if not bucket_name:
        flash("Bucket name is required.")
        return redirect(url_for('index'))

    if bucket_name == 'my-files':
        flash("Cannot delete the default bucket 'my-files'.")
        return redirect(url_for('index', bucket=bucket_name))

    try:
        def collect_all_files(prefix="", collected_files=None):
            if collected_files is None:
                collected_files = []

            list_res = supabase.storage.from_(bucket_name).list(prefix, {"limit": 1000})
            if isinstance(list_res, list):
                items = list_res
            elif isinstance(list_res, dict) and list_res.get('data'):
                items = list_res['data']
            else:
                return collected_files

            for item in items:
                if item and isinstance(item, dict) and item.get("name"):
                    item_path = f"{prefix.rstrip('/')}/{item['name']}" if prefix else item["name"]

                    if item.get("metadata") is not None:
                        collected_files.append(item_path)
                    else:
                        collect_all_files(item_path, collected_files)
                        collected_files.append(f"{item_path}/.keep")

            return collected_files

        all_files = collect_all_files()
        batch_size = 100
        for i in range(0, len(all_files), batch_size):
            batch = all_files[i:i + batch_size]
            try:
                supabase.storage.from_(bucket_name).remove(batch)
            except:
                pass

        res = supabase.storage.delete_bucket(bucket_name)

        if isinstance(res, dict):
            if res.get("error"):
                error_msg = res['error'].get('message', str(res['error']))
                flash(f"Error deleting bucket: {error_msg}")
            elif res.get("statusCode") and res["statusCode"] >= 400:
                flash(f"Error deleting bucket: {res.get('message', 'Unknown error')}")
            else:
                flash(f"Bucket '{bucket_name}' deleted successfully.")
                
                available_buckets = get_available_buckets()
                new_bucket = available_buckets[0] if available_buckets else 'my-files'
                return redirect(url_for('index', bucket=new_bucket))
        else:
            flash(f"Bucket '{bucket_name}' deleted successfully.")
            available_buckets = get_available_buckets()
            new_bucket = available_buckets[0] if available_buckets else 'my-files'
            return redirect(url_for('index', bucket=new_bucket))

    except Exception as e:
        error_msg = str(e)
        flash(f"Error deleting bucket: {error_msg}")

    return redirect(url_for('index', bucket=bucket_name))


@app.route('/switch_bucket')
def switch_bucket():
    bucket_name = request.args.get('bucket', 'my-files')
    return redirect(url_for('index', bucket=bucket_name))


@app.route('/list_buckets')
def list_buckets():
    try:
        buckets_res = supabase.storage.list_buckets()
        buckets = []

        if isinstance(buckets_res, list):
            buckets = buckets_res
        elif isinstance(buckets_res, dict) and buckets_res.get('data'):
            buckets = buckets_res['data']

        return jsonify({"buckets": buckets})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)