import json
import numpy as np

with open('output.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

polygons = data['polygon']
texts = data['texts']

targets = ["신장", "체중", "골격근량", "체지방량"]

print(f"Total texts: {len(texts)}")

for target in targets:
    found = False
    for i, text in enumerate(texts):
        if target in text:
            poly = np.array(polygons[i])
            y_min = poly[:, 1].min()
            y_max = poly[:, 1].max()
            center_y = (y_min + y_max) / 2
            print(f"Found '{text}' at index {i}. Y range: {y_min}-{y_max}, Center Y: {center_y}")
            found = True
    if not found:
        print(f"Target '{target}' NOT found in texts.")
