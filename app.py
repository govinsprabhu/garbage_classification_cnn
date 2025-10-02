import os
from datetime import datetime
from typing import Dict, Any

from flask import Flask, request, jsonify, render_template, send_from_directory
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.layers import Input


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

# Constants
labels =['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash']

# Recycling rates in USD per kg
RECYCLING_RATES = {
    'cardboard': 0.10,  # $0.10 per kg
    'glass': 0.15,      # $0.15 per kg
    'metal': 2.00,      # $2.00 per kg
    'paper': 0.20,      # $0.20 per kg
    'plastic': 0.30,    # $0.30 per kg
    'trash': 0.00       # No value for general trash
}

# Recycling tips
RECYCLING_TIPS = {
    'cardboard': 'Flatten boxes to save space. Remove any tape or staples.',
    'glass': 'Rinse containers. Sort by color if required by your recycling center.',
    'metal': 'Clean and crush cans to save space. Remove any non-metal parts.',
    'paper': 'Keep paper dry and clean. Remove any plastic wrapping.',
    'plastic': 'Check the recycling number. Rinse containers. Remove caps if different material.',
    'trash': 'Consider if any parts could be recycled separately.'
}


def ensure_directories_exist() -> None:

    os.makedirs(UPLOADS_DIR, exist_ok=True)


def load_ml_model():
    MODEL_PATH = os.path.join(BASE_DIR, "garbage_classification_model.h5")
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
            
        # Try loading the model with custom objects
        import tensorflow as tf
        print(f"TensorFlow version: {tf.__version__}")
        
        # Let's try the alternate model file which might be more compatible
        MODEL_PATH = os.path.join(BASE_DIR, "garbage_classification_model.h5")
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

def create_app() -> Flask:
    # Load the model when creating the app
    model = load_ml_model()
    
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
        nonlocal model  # Access the model from the outer scope
        
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
        
        # Get recycling information
        recycling_rate = RECYCLING_RATES[label]
        recycling_tip = RECYCLING_TIPS[label]
        
        return jsonify({
            "filename": image_file.filename,
            "saved_as": safe_name,
            "prediction": {
                "label": label,
                "probabilities": {labels[i]: float(prob) for i, prob in enumerate(probabilities)},
                "recycling_info": {
                    "rate_per_kg": recycling_rate,
                    "example_earnings": {
                        "1kg": recycling_rate * 1,
                        "5kg": recycling_rate * 5,
                        "10kg": recycling_rate * 10
                    },
                    "tip": recycling_tip
                }
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


