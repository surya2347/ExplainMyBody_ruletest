import json
import ast
import os

input_file = r'c:\EPMB\ExplainMyBody_ruletest\experiments\OCRtxt_postprocessing\rawdata.txt'
output_file = r'c:\EPMB\ExplainMyBody_ruletest\experiments\OCRtxt_postprocessing\output.json'

data = {
    "polygon": [],
    "texts": []
}

if not os.path.exists(input_file):
    print(f"Error: {input_file} not found.")
else:
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Split by " | Box: "
            if " | Box: " in line:
                parts = line.split(" | Box: ")
                text_part = parts[0]
                box_part = parts[1]
                
                # Extract text
                # Format: [X.XX] Text
                if "] " in text_part:
                    text = text_part.split("] ", 1)[1]
                else:
                    # Fallback if the format is slightly different
                    text = text_part
                
                # Extract box coordinates
                try:
                    # Using ast.literal_eval is safe for this format
                    polygon = ast.literal_eval(box_part)
                except Exception as e:
                    print(f"Error parsing box on line: {line}")
                    print(e)
                    polygon = box_part # Fallback to string
                
                data["polygon"].append(polygon)
                data["texts"].append(text)

    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Successfully processed {len(data['texts'])} entries and saved to {output_file}")
