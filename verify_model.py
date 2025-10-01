import os
import tensorflow as tf
from tensorflow.keras.models import load_model

def verify_model():
    model_path = os.environ.get('MODEL_PATH', 'garbage_classification_model.h5')
    print(f"Verifying model at: {model_path}")
    
    if not os.path.exists(model_path):
        print(f"ERROR: Model file not found at {model_path}")
        return False
        
    try:
        model = load_model(model_path, compile=False)
        print("Model loaded successfully!")
        model.summary()
        return True
    except Exception as e:
        print(f"ERROR loading model: {e}")
        return False

if __name__ == "__main__":
    verify_model()
