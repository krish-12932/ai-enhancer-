import os
import time
import threading
import sys
from flask import Flask, render_template, request, send_from_directory, jsonify
from PIL import Image
import cv2
import numpy as np
import traceback

# HACK: Fix for basicsr compatibility with newer torchvision
# basicsr often fails with newer torch because it tries to import 'functional_tensor'
import torchvision.transforms.functional as F
try:
    from torchvision.transforms import functional_tensor
except ImportError:
    # Create a dummy module to satisfy basicsr imports
    import types
    sys.modules['torchvision.transforms.functional_tensor'] = types.ModuleType('functional_tensor')
    sys.modules['torchvision.transforms.functional_tensor'].rgb_to_grayscale = F.rgb_to_grayscale

# Try importing RealESRGAN dependencies
try:
    from realesrgan import RealESRGANer
    from basicsr.archs.rrdbnet_arch import RRDBNet
    HAS_AI = True
    print("SUCCESS: RealESRGAN libraries loaded successfully.")
except Exception as e:
    HAS_AI = False
    print("WARNING: RealESRGAN load failed. Fallback enabled.")
    traceback.print_exc()

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
WEIGHTS_DIR = 'weights'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(WEIGHTS_DIR, exist_ok=True)

# Cleanup function to remove old files
def cleanup_files():
    while True:
        try:
            now = time.time()
            for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER]:
                for filename in os.listdir(folder):
                    filepath = os.path.join(folder, filename)
                    if os.path.isfile(filepath):
                        # Remove files older than 10 minutes
                        if now - os.path.getmtime(filepath) > 600: 
                            try:
                                os.remove(filepath)
                            except PermissionError:
                                pass # File might be in use
        except Exception as e:
            print(f"Error in cleanup: {e}")
        time.sleep(60)

threading.Thread(target=cleanup_files, daemon=True).start()

def get_target_dimensions(width, height):
    """
    Calculate target dimensions such that the longer side is exactly 3840px.
    Preserves aspect ratio.
    """
    if width >= height:
        target_width = 3840
        aspect_ratio = height / width
        target_height = int(target_width * aspect_ratio)
    else:
        target_height = 3840
        aspect_ratio = width / height
        target_width = int(target_height * aspect_ratio)
    return target_width, target_height

def upscale_image_ai(input_path, output_path, target_w, target_h):
    """
    Attempt to use RealESRGAN for upscaling, then resize to exact target.
    """
    if not HAS_AI:
        return False
    
    try:
        # Load model using RealESRGAN (x4 model)
        # We need the model weights file. RealESRGANer usually downloads it if passed correct args,
        # or we might need to point to it. Default logic often looks for it.
        # Minimal setup for RealESRGANer:
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        
        # This will auto-download 'RealESRGAN_x4plus.pth' to weights dir if not present
        upsampler = RealESRGANer(
            scale=4,
            model_path='https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth',
            model=model,
            tile=400, # Tile size to save memory
            tile_pad=10,
            pre_pad=0,
            half=False # Use float32 (better for CPU)
        )
        
        img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
        
        # Upscale x4
        output, _ = upsampler.enhance(img, outscale=4)
        
        # Now resize to the exact target 4K dimensions requested
        # RealESRGAN x4 might result in > 4K or < 4K depending on input.
        # We resize the high-quality AI output to our target 3840px standard.
        output_resized = cv2.resize(output, (target_w, target_h), interpolation=cv2.INTER_AREA)
        
        cv2.imwrite(output_path, output_resized)
        return True
    except Exception as e:
        print(f"AI Upscaling Runtime Error: {e}")
        traceback.print_exc()
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = f"{int(time.time())}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        processed_filename = f"upscaled_{filename}"
        processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)
        
        final_w, final_h = 0, 0
        
        try:
            # Open original to get size
            with Image.open(filepath) as img:
                orig_w, orig_h = img.size
                final_w, final_h = get_target_dimensions(orig_w, orig_h)
            
            # Attempt AI Upscale
            success = upscale_image_ai(filepath, processed_path, final_w, final_h)
            
            
            # Fallback to PIL if AI failed or not available
            if not success:
                print("Using Standard High-Quality Resizing (Fallback)")
                with Image.open(filepath) as img:
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    
                    # High quality Lanczos resize
                    # Ensure we use the CALCULATED dimensions to preserve aspect ratio
                    img_resized = img.resize((final_w, final_h), Image.Resampling.LANCZOS)
                    img_resized.save(processed_path, quality=95)
            
            return jsonify({
                'success': True, 
                'filename': processed_filename,
                'width': final_w,
                'height': final_h
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
