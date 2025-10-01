import os
from datetime import datetime
from typing import Dict, Any

from flask import Flask, request, jsonify, render_template, send_from_directory
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

# Load model once
MODEL_PATH = os.path.join(BASE_DIR, "garbage_classification_model.h5")
labels =['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash']

def load_ml_model():
    try:
        print(f"Current working directory: {os.getcwd()}")
        print(f"BASE_DIR: {BASE_DIR}")
        print(f"Looking for model at: {MODEL_PATH}")
        
        # List all files in the current directory
        print("Files in current directory:")
        for f in os.listdir(BASE_DIR):
            print(f"- {f}")
        
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
            
        file_size = os.path.getsize(MODEL_PATH)
        print(f"Model file size: {file_size} bytes")
        
        if file_size == 0:
            raise ValueError("Model file is empty")
            
        # Try loading the model
        import tensorflow as tf
        print(f"TensorFlow version: {tf.__version__}")
        model = load_model(MODEL_PATH, compile=False)
        print("Model loaded successfully!")
        
        # Print model details
        print("\nModel Summary:")
        model.summary()
        
        return model
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        return None

model = load_ml_model()


def ensure_directories_exist() -> None:

    os.makedirs(UPLOADS_DIR, exist_ok=True)


def create_app() -> Flask:

    ensure_directories_exist()
    app = Flask(__name__, static_folder=STATIC_DIR, template_folder=TEMPLATES_DIR)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/health", methods=["GET"])
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.route("/predict", methods=["POST"]) 
    def predict() -> Any:
        # Expecting a file field named 'image'
        if "image" not in request.files:
            return jsonify({"error": "No image file provided. Use form field 'image'."}), 400

        image_file = request.files["image"]
        if image_file.filename == "":
            return jsonify({"error": "Empty filename."}), 400

        # Save the upload to disk with a timestamped filename
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
        safe_name = f"upload_{timestamp}_{image_file.filename}"
        save_path = os.path.join(UPLOADS_DIR, safe_name)
        image_file.save(save_path)
        # Actual model prediction logic
        if model is None:
            return jsonify({"error": "Model not loaded."}), 500
        # Load and preprocess image
        img = image.load_img(save_path, target_size=(300, 300))  # Update size if needed
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = x / 255.0
        print("Model expects:", model.input_shape)
        print("Input shape:", x.shape)
        preds = model.predict(x)
        print("Prediction:", preds)
        predicted_class = np.argmax(preds[0])  # Get index of highest probability
        probabilities = preds[0].tolist()  # Convert to list for JSON
        print("Predicted class index:", predicted_class)
        label = labels[predicted_class]
        
        return jsonify({
            "filename": image_file.filename,
            "saved_as": safe_name,
            "prediction": {
                "label": label,
                "probabilities": {labels[i]: float(prob) for i, prob in enumerate(probabilities)}
            }
        })

    @app.route("/uploads/<path:filename>")
    def get_upload(filename: str):
        return send_from_directory(UPLOADS_DIR, filename)

    return app


if __name__ == "__main__":
    # Allow overriding host/port via env vars
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("DEBUG", "true").lower() == "true"
    app = create_app()
    app.run(host=host, port=port, debug=debug)


