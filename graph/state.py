from typing import List, TypedDict, Optional

class HairState(TypedDict):
    # Input
    user_id: str
    image_path: str
    is_first_image: bool

    # Processing
    head_detected: bool
    bbox: Optional[List[int]]
    head_crop_path: Optional[str]
    confidence: Optional[float]

    # Analysis
    previous_image_path: Optional[str]
    analysis_result: Optional[str]

    # Output
    report: Optional[str]
    error: Optional[str]