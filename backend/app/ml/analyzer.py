from ultralytics import YOLO
from PIL import Image
import io

model = YOLO(r"E:/Hackthons/Road Safety/model/runs/detect/roadwatch_model-5/weights/best.pt")

# Classes to ignore
IGNORE_CLASSES = ["road_marking_blur"]

CLASS_BASE_SEVERITY = {
    "pothole"            : 3,
    "alligator_crack"    : 2,
    "transverse_crack"   : 1,
    "longitudinal_crack" : 1,
}

SEVERITY_MAP = {
    1: "Low",
    2: "Medium",
    3: "High",
    4: "Critical"
}

SLA_MAP = {
    "Low"      : "30 days",
    "Medium"   : "15 days",
    "High"     : "7 days",
    "Critical" : "48 hours"
}

AUTHORITY_MAP = {
    "Low"      : "Assistant Engineer",
    "Medium"   : "Assistant Executive Engineer",
    "High"     : "Executive Engineer",
    "Critical" : "Senior Authority — Immediate Escalation"
}

def calculate_severity(class_name, confidence, box_area_ratio):
    base = CLASS_BASE_SEVERITY.get(class_name, 1)

    if box_area_ratio > 0.15:
        base += 1

    if confidence > 0.80:
        base += 1

    return SEVERITY_MAP[min(base, 4)]


def analyze_image(image_bytes):
    image    = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_area = image.width * image.height

    results  = model.predict(source=image, conf=0.25, verbose=False)

    detections = []

    for result in results:
        for box in result.boxes:
            class_id   = int(box.cls)
            confidence = float(box.conf)
            class_name = model.names[class_id]

            # Skip ignored classes
            if class_name in IGNORE_CLASSES:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            box_area        = (x2 - x1) * (y2 - y1)
            box_area_ratio  = box_area / img_area

            severity = calculate_severity(class_name, confidence, box_area_ratio)

            detections.append({
                "damage_type" : class_name.replace("_", " ").title(),
                "confidence"  : round(confidence * 100, 1),
                "severity"    : severity,
                "sla"         : SLA_MAP[severity],
                "route_to"    : AUTHORITY_MAP[severity],
                "bbox"        : [round(x1), round(y1), round(x2), round(y2)],
            })

    if not detections:
        return {
            "status"     : "no_damage_detected",
            "severity"   : None,
            "detections" : []
        }

    severity_order = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    worst = max(detections, key=lambda x: severity_order[x["severity"]])

    return {
        "status"           : "damage_detected",
        "total_detections" : len(detections),
        "worst_severity"   : worst["severity"],
        "sla"              : worst["sla"],
        "route_to"         : worst["route_to"],
        "detections"       : detections
    }