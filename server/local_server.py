from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
import tempfile
from datetime import datetime, timedelta

# Set up paths - works from any director
HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))
ML_CODE = os.path.join(REPO_ROOT, "ml", "code")
MODEL_PATH = os.path.join(REPO_ROOT, "ml", "models", "model.h5")
OUTPUT_DIR = os.path.join(REPO_ROOT, "output")

# Add ML code to Python path
sys.path.append(ML_CODE)

# Load ML dependencies and model
try:
    from util import (
        load_model,
        resize_image,
        fix_dims,
        predict_color,
        upscale_color,
        rgb_to_byte_arr,
    )
    import hyperparameters as hp
    from skimage.io import imread

    MODEL = load_model(MODEL_PATH)
    print("ML Model loaded successfully!")
except ImportError as e:
    print(f"Error loading ML model: {e}")
    print("Make sure you're in the repo root and ML dependencies are installed.")
    sys.exit(1)
except Exception as e:
    print(f"Error loading model file: {e}")
    print(f"Looking for model at: {MODEL_PATH}")
    sys.exit(1)

app = Flask(__name__)
CORS(app)  # Allow frontend to call this API

# In-memory storage for local dev
users = {}
images = {}


def load_existing_images():
    """Load existing images from the output directory"""
    if os.path.exists(OUTPUT_DIR):
        for filename in os.listdir(OUTPUT_DIR):
            # Only load our generated images
            if filename.startswith("local_") and filename.endswith(".png"):
                image_id = filename.replace(".png", "")
                image_path = os.path.join(OUTPUT_DIR, filename)
                images[image_id] = {
                    "path": image_path,
                    "key": "demo-key",
                    "created": datetime.fromtimestamp(os.path.getctime(image_path)),
                }
                print(f"📸 Loaded existing image: {image_id}")


# Load any existing images on startup
load_existing_images()

@app.route("/api", methods=["GET"])
def api_root():
    return "Ok"


@app.route("/api/user/create", methods=["POST"])
def create_user():
    """Create a user (simplified for local development)"""
    data = request.get_json()
    key = data.get("key", "demo-key")

    print(f"👤 Creating user with key: {key}")

    # Give unlimited balance for local dev
    users[key] = {"balance": 999, "refresh": datetime.now() + timedelta(hours=1)}

    print(f"User created. Total users: {len(users)}")
    return jsonify({"status": 200, "message": "User created"}), 200


@app.route("/api/user/balance/<key>", methods=["GET"])
def get_balance(key):
    """Get user balance"""
    # Auto-create user if they don't exist
    if key not in users:
        users[key] = {"balance": 999, "refresh": datetime.now() + timedelta(hours=1)}

    user = users[key]
    return jsonify(
        {
            "status": 200,
            "balance": user["balance"],
            "refresh": user["refresh"].isoformat(),
            "message": "Success",
        }
    )


@app.route("/api/image/colorize/<key>", methods=["POST"])
def colorize_image(key):
    """Colorize an image using the local ML model"""
    print(f"Colorize request for key: {key}")
    print(f"Available users: {list(users.keys())}")

    # Check if user exists
    if key not in users:
        print(f"User {key} not found")
        return jsonify({"message": "User not found"}), 403

    # Validate image upload
    if "image" not in request.files:
        return jsonify({"message": "No image provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"message": "No image selected"}), 400

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            file.save(tmp_file.name)

            # Load and process image
            img = imread(tmp_file.name)
            img = fix_dims(img)

            # Run ML colorization pipeline
            downscaled_img = resize_image(img, (hp.img_size, hp.img_size))
            colored_lab = predict_color(downscaled_img, MODEL)
            upscaled_rgb = upscale_color(img, colored_lab)

            # Make sure output directory exists
            os.makedirs(OUTPUT_DIR, exist_ok=True)

            # Generate unique filename
            image_id = f"local_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            colorized_path = os.path.join(OUTPUT_DIR, f"{image_id}.png")

            # Save the colorized image
            colorized_bytes = rgb_to_byte_arr(upscaled_rgb)
            data_bytes = colorized_bytes.getvalue()
            with open(colorized_path, "wb") as f:
                f.write(data_bytes)

            # Track this image
            images[image_id] = {
                "path": colorized_path,
                "key": key,
                "created": datetime.now(),
            }

            # Clean up temp file
            os.unlink(tmp_file.name)

            # Return success response with image info
            return jsonify(
                {
                    "status": 200,
                    "remainingBalance": users[key]["balance"],
                    "refresh": users[key]["refresh"].isoformat(),
                    "message": "Success",
                    "imageId": image_id,
                    "download": f"http://localhost:4000/api/image/get/{image_id}",
                    "redirect": f"http://localhost:3000/#image={image_id}",
                }
            )

    except Exception as e:
        print(f"Error colorizing image: {e}")
        return jsonify({"message": "Colorization failed"}), 500


@app.route("/api/image/get/<image_id>", methods=["GET"])
def get_image(image_id):
    """Get a colorized image"""
    # Check if we know about this image
    if image_id not in images:
        return jsonify({"message": "Image not found"}), 404

    image_path = images[image_id]["path"]
    # Make sure file still exists on disk
    if not os.path.exists(image_path):
        return jsonify({"message": "Image file not found"}), 404

    # Read and return image data
    with open(image_path, "rb") as f:
        image_data = f.read()

    return jsonify(
        {
            "status": 200,
            "message": "Success",
            "colored": {"data": list(image_data)},
        }
    )


# Simple stats endpoints for debugging
@app.route("/api/user/total", methods=["GET"])
def get_total_users():
    return jsonify({"total": len(users)})


@app.route("/api/image/total", methods=["GET"])
def get_total_images():
    return jsonify({"total": len(images)})


@app.route("/api/image/list", methods=["GET"])
def list_images():
    return jsonify({"images": list(images.keys())})


# Serve React app for production
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react_app(path):
    """Serve the React app for all non-API routes"""
    if path.startswith("api/"):
        # Let API routes be handled by their specific handlers
        return jsonify({"message": "API route not found"}), 404
    
    # Serve React build files
    build_dir = os.path.join(REPO_ROOT, "client", "build")
    if os.path.exists(build_dir):
        if path and os.path.exists(os.path.join(build_dir, path)):
            return send_from_directory(build_dir, path)
        else:
            return send_from_directory(build_dir, "index.html")
    else:
        return "React build not found. Run 'npm run build' in the client directory.", 500


if __name__ == "__main__":
    print("Frontend: http://localhost:3000")
    print("Backend: http://localhost:4000")
    print("ML Model: Loaded and ready!")
    print("=" * 50)

    app.run(host="0.0.0.0", port=4000, debug=True)
