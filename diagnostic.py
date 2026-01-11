
try:
    import torch
    print(f"Torcb: {torch.__version__}, CUDA: {torch.cuda.is_available()}")
except ImportError:
    print("Torch not found")

try:
    import torchvision
    print(f"Torchvision: {torchvision.__version__}")
except ImportError:
    print("Torchvision not found")

try:
    import basicsr
    print("Basicsr found")
except ImportError:
    print("Basicsr not found")

try:
    import realesrgan
    print("RealESRGAN found")
except ImportError:
    print("RealESRGAN not found")

try:
    import cv2
    print(f"OpenCV: {cv2.__version__}")
except ImportError:
    print("OpenCV not found")
