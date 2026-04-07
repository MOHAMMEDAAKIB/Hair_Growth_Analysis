import json
from pathlib import Path

def convert_labelme_to_yolo(image_dir, output_dir):
    json_files = list(Path(image_dir).glob("*.json"))
    
    if len(json_files) == 0:
        print(f"⚠️ No JSON files found in {image_dir}")
        return
    
    for json_file in json_files:
        with open(json_file) as f:
            data = json.load(f)
        
        img_w = data["imageWidth"]
        img_h = data["imageHeight"]
        yolo_lines = []
        
        for shape in data["shapes"]:
            if shape["shape_type"] != "rectangle":
                print(f"⚠️ Skipping polygon in {json_file.name}")
                continue
            if shape["label"] != "head":
                continue
            
            pts = shape["points"]
            x1, y1 = pts[0]
            x2, y2 = pts[1]
            
            x_center = ((x1 + x2) / 2) / img_w
            y_center = ((y1 + y2) / 2) / img_h
            width    = abs(x2 - x1) / img_w
            height   = abs(y2 - y1) / img_h
            
            yolo_lines.append(
                f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
            )
        
        out_file = Path(output_dir) / (json_file.stem + ".txt")
        with open(out_file, "w") as f:
            f.write("\n".join(yolo_lines))
        
        print(f"✅ {json_file.name} → {out_file.name}")
    
    print(f"\n🎉 Done! {len(json_files)} files converted!")

# Convert
print("📂 Converting Train...")
convert_labelme_to_yolo(
    "dataset/images/train",
    "dataset/labels/train"
)

print("\n📂 Converting Val...")
convert_labelme_to_yolo(
    "dataset/images/val",
    "dataset/labels/val"
)