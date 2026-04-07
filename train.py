from ultralytics import YOLO # type: ignore

model = YOLO("yolov8n.pt")

results = model.train(
    data="data.yaml",
    epochs=50,
    imgsz=640,
    batch=8,
    name="head_detect"
)

print("✅ Training Done!")
print("📁 Model: runs/detect/head_detect/weights/best.pt")