"""
Storage Management Routes for Biped Platform
Handles file operations and storage monitoring
"""

import mimetypes
import os

from flask import Blueprint, jsonify, request, send_file
from src.utils.storage import storage_manager
from werkzeug.utils import secure_filename

storage_bp = Blueprint("storage", __name__, url_prefix="/api/storage")


@storage_bp.route("/info", methods=["GET"])
def get_storage_info():
    """Get storage usage information"""
    try:
        info = storage_manager.get_storage_info()
        return jsonify({"success": True, "data": info})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@storage_bp.route("/upload", methods=["POST"])
def upload_file():
    """Upload a file to the storage system"""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400

        file = request.files["file"]
        category = request.form.get("category", "general")

        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400

        # Save the file
        relative_path = storage_manager.save_uploaded_file(file, category)

        if relative_path:
            return jsonify(
                {
                    "success": True,
                    "data": {
                        "filename": file.filename,
                        "path": relative_path,
                        "category": category,
                        "url": f"/api/storage/file/{relative_path}",
                    },
                }
            )
        else:
            return jsonify({"success": False, "error": "Failed to save file"}), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@storage_bp.route("/file/<path:relative_path>", methods=["GET"])
def serve_file(relative_path):
    """Serve a file from storage"""
    try:
        file_path = storage_manager.get_file_path(relative_path)

        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": "File not found"}), 404

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(file_path)

        return send_file(file_path, mimetype=mime_type, as_attachment=False)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@storage_bp.route("/file/<path:relative_path>", methods=["DELETE"])
def delete_file(relative_path):
    """Delete a file from storage"""
    try:
        success = storage_manager.delete_file(relative_path)

        if success:
            return jsonify({"success": True, "message": "File deleted successfully"})
        else:
            return (
                jsonify({"success": False, "error": "File not found or could not be deleted"}),
                404,
            )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@storage_bp.route("/files", methods=["GET"])
def list_files():
    """List files in storage"""
    try:
        category = request.args.get("category")
        files = storage_manager.list_files(category)

        return jsonify(
            {"success": True, "data": {"files": files, "count": len(files), "category": category}}
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@storage_bp.route("/backup", methods=["POST"])
def create_backup():
    """Create a database backup"""
    try:
        # Get database path from app config
        from flask import current_app

        db_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")

        if db_uri.startswith("sqlite:///"):
            db_path = db_uri.replace("sqlite:///", "")
            backup_path = storage_manager.backup_database(db_path)

            if backup_path:
                return jsonify(
                    {
                        "success": True,
                        "data": {
                            "backup_path": backup_path,
                            "message": "Database backup created successfully",
                        },
                    }
                )
            else:
                return jsonify({"success": False, "error": "Failed to create backup"}), 500
        else:
            return (
                jsonify({"success": False, "error": "Database backup only supported for SQLite"}),
                400,
            )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@storage_bp.route("/health", methods=["GET"])
def storage_health():
    """Check storage system health"""
    try:
        info = storage_manager.get_storage_info()

        # Check if we can write to the data directory
        test_file = os.path.join(storage_manager.data_dir, ".health_check")
        try:
            with open(test_file, "w") as f:
                f.write("health_check")
            os.remove(test_file)
            write_access = True
        except:
            write_access = False

        return jsonify(
            {
                "success": True,
                "data": {
                    "storage_accessible": True,
                    "write_access": write_access,
                    "data_directory": storage_manager.data_dir,
                    "storage_info": info,
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e), "storage_accessible": False}), 500
