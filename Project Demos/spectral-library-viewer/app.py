"""
Spectral Library Viewer - Production Flask Application

A web-based spectral library viewer for visualizing mineral, vegetation,
and material spectra from CSV, SLI (ENVI), and ASCII file formats.
"""

import os
import json
import traceback

from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from parsers import parse_csv, parse_sli, parse_ascii

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB max upload
app.config["UPLOAD_FOLDER"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "uploads"
)

ALLOWED_EXTENSIONS = {"csv", "sli", "hdr", "txt", "asc", "ascii", "dat", "sed"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Handle spectral file uploads and return parsed data."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    files = request.files.getlist("file")
    if not files or files[0].filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Separate main data files from header files
    main_files = []
    hdr_files = {}

    for f in files:
        if not allowed_file(f.filename):
            return jsonify({"error": f"File type not allowed: {f.filename}"}), 400
        fname = secure_filename(f.filename)
        ext = fname.rsplit(".", 1)[1].lower()
        if ext == "hdr":
            base = fname.rsplit(".", 1)[0].lower()
            hdr_files[base] = f.read()
        else:
            main_files.append((fname, ext, f.read()))

    all_results = []

    for fname, ext, content in main_files:
        try:
            if ext == "csv":
                result = parse_csv(content, fname)
            elif ext == "sli":
                base = fname.rsplit(".", 1)[0].lower()
                hdr = hdr_files.get(base)
                result = parse_sli(content, fname, hdr_content=hdr)
            else:
                result = parse_ascii(content, fname)

            all_results.append(result)

        except Exception as e:
            traceback.print_exc()
            return jsonify({"error": f"Error parsing {fname}: {str(e)}"}), 400

    if not all_results:
        return jsonify({"error": "No valid spectral files found"}), 400

    # Merge results if multiple files
    if len(all_results) == 1:
        return jsonify(all_results[0])

    merged = {
        "wavelengths": all_results[0]["wavelengths"],
        "spectra": [],
        "metadata": {
            "filename": ", ".join(r["metadata"]["filename"] for r in all_results),
            "format": "Multiple files",
            "num_spectra": 0,
            "num_bands": len(all_results[0]["wavelengths"]),
            "wavelength_unit": "nm",
        },
    }
    for r in all_results:
        merged["spectra"].extend(r["spectra"])
    merged["metadata"]["num_spectra"] = len(merged["spectra"])
    return jsonify(merged)


@app.route("/api/sample-library")
def sample_library():
    """Return built-in sample spectral library data."""
    sample_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "static",
        "data",
        "sample_library.json",
    )
    if os.path.exists(sample_path):
        with open(sample_path, "r") as f:
            return jsonify(json.load(f))
    return jsonify({"error": "Sample library not found"}), 404


@app.route("/api/health")
def health():
    return jsonify({"status": "healthy", "version": "1.0.0"})


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
