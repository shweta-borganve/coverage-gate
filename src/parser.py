from dataclasses import dataclass
import xml.etree.ElementTree as ET

@dataclass
class CoverageMetrics:
    total_coverage: float

def parse_cobertura(file_path: str) -> CoverageMetrics:
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    line_rate = float(root.get("line-rate", 0))
    total_coverage = line_rate * 100
    
    return CoverageMetrics(total_coverage=total_coverage) 