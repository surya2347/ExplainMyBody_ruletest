"""
인바디 결과지 종합 매칭 - 보정 기능 포함 및 22개 항목 추출
"""

import os
# import cv2
import json
import re
import numpy as np
import time
# from paddleocr import PaddleOCR

class InBodyMatcher:
    def __init__(self):
        # 환경 변수 설정
        os.environ['FLAGS_use_mkldnn'] = '0'
        os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
        
        print("OCR 엔진 초기화 중 (보정 기능 활성화)...")
        # 보정을 위해 use_textline_orientation 활성화
        # self.ocr = PaddleOCR(
        #     lang='korean',
        #     use_textline_orientation=True
        # )

    def extract_and_match(self, image_path):
        start_time = time.time()
        print(f"이미지 분석 및 보정 시작: {os.path.basename(image_path)}")
        
        # 1. OCR 실행 (predict 메서드는 보정 로직이 더 잘 통합되어 있습니다)
        result = self.ocr.predict(input=image_path)
        np.set_printoptions(threshold=np.inf)

        
        all_nodes = []
        if result:
            for res in result:
                if 'dt_polys' not in res or 'rec_texts' not in res:
                    continue
                
                polygons = res['dt_polys']
                texts = res['rec_texts']
                # scores = res.get('rec_scores', [1.0] * len(texts))
                
                # for polygon, text, confidence in zip(polygons, texts, scores):
                for polygon, text in zip(polygons, texts):
                    pts = np.array(polygon)
                    
                    # print(pts)
                    x_min, y_min = pts.min(axis=0)
                    x_max, y_max = pts.max(axis=0)
                    # print("min, max : ", x_min, y_min, x_max, y_max)
                    
                    all_nodes.append({
                        'text': text.strip(),
                        'bbox': [int(x_min), int(y_min), int(x_max), int(y_max)],
                        'center': [(x_min + x_max) / 2, (y_min + y_max) / 2],
                        # 'conf': float(confidence)
                    })

        # 2. 매칭 규칙 정의 (요청하신 22개 항목)
        targets = {
            "신장": {"dir": "down", "re": r"(\d+\.?\d*)", "unit": "cm", "dist": 300},
            "연령": {"dir": "down", "re": r"(\d+)", "unit": "세", "dist": 300},
            "성별": {"dir": "down", "re": r"(남성|여성|남|여)", "unit": "", "dist": 300},
            "체수분": {"dir": "right", "re": r"(\d+\.\d+)", "unit": "L", "dist": 400},
            "단백질": {"dir": "right", "re": r"(\d+\.\d+)", "unit": "kg", "dist": 400},
            "무기질": {"dir": "right", "re": r"(\d+\.\d+)", "unit": "kg", "dist": 400},
            "체지방": {"dir": "right", "re": r"(\d+\.\d+)", "unit": "kg", "dist": 400},
            "체중": {"dir": "right", "re": r"(\d+\.\d+)", "unit": "kg", "dist": 500},
            "골격근량": {"dir": "right", "re": r"(\d+\.\d+)", "unit": "kg", "dist": 500},
            "체지방량": {"dir": "right", "re": r"(\d+\.\d+)", "unit": "kg", "dist": 500},
            "BMI": {"dir": "right", "re": r"(\d+\.\d+)", "unit": "kg/m²", "dist": 500},
            "체지방률": {"dir": "right", "re": r"(\d+\.\d+)", "unit": "%", "dist": 500},
            "적정체중": {"dir": "right", "re": r"(\d+\.\d+)", "unit": "kg", "dist": 400},
            "체중조절": {"dir": "right", "re": r"([+-]?\d+\.?\d*)", "unit": "kg", "dist": 400},
            "지방조절": {"dir": "right", "re": r"([+-]?\d+\.?\d*)", "unit": "kg", "dist": 400},
            "근육조절": {"dir": "right", "re": r"([+-]?\d+\.?\d*)", "unit": "kg", "dist": 400},
            "복부지방률": {"dir": "down", "re": r"(\d\.\d{2})", "unit": "", "dist": 400},
            "내장지방레벨": {"dir": "down", "re": r"(\d+)", "unit": "Level", "dist": 400},
            "제지방량": {"dir": "right", "re": r"(\d+\.\d+)", "unit": "kg", "dist": 400},
            "기초대사량": {"dir": "right", "re": r"(\d+)", "unit": "kcal", "dist": 400},
            "비만도": {"dir": "right", "re": r"(\d+)", "unit": "%", "dist": 400},
            "권장섭취열량": {"dir": "right", "re": r"(\d+)", "unit": "kcal", "dist": 400},
        }

        matched_data = {}
        
        print("\n" + "="*60)
        print(f"{'항목명':<15} | {'추출된 값':<15} | {'상태'}")
        print("-" * 60)

        for key, config in targets.items():
            # 키워드 노드 찾기
            keyword_node = None
            for node in all_nodes:
                if key in node['text']:
                    keyword_node = node
                    break
            
            if not keyword_node:
                matched_data[key] = None
                print(f"{key:<15} | {'-':<15} | ❌ 키워드 미발견")
                continue

            k_center = keyword_node['center']
            k_bbox = keyword_node['bbox']
            k_height = k_bbox[3] - k_bbox[1]
            k_width = k_bbox[2] - k_bbox[0]
            
            # Y축 허용 범위 (키워드 높이의 80%를 기준으로 중심점 간 거리 체크) 130%
            y_threshold = k_height * 0.8
            
            candidates = []
            for item in all_nodes:
                if item == keyword_node: continue
                
                i_center = item['center']
                i_bbox = item['bbox']
                
                # 방향에 따른 필터링
                if config['dir'] == 'right':
                    # 1. 동일 Y축 상에 있는지 확인 (키워드 높이의 80% 기준)
                    y_threshold = k_height * 0.8
                    if abs(i_center[1] - k_center[1]) > y_threshold:
                        continue
                    # 2. 키워드보다 오른쪽에 있는지 확인 (키워드 우측 끝 기준)
                    if i_center[0] < k_bbox[2]:
                        continue
                
                elif config['dir'] == 'down':
                    # 1. 동일 X축 상에 있는지 확인 (키워드 너비의 80% 기준)
                    x_threshold = k_width * 0.8
                    if abs(i_center[0] - k_center[0]) > x_threshold:
                        continue
                    # 2. 키워드보다 아래쪽에 있는지 확인 (키워드 하단 끝 기준)
                    if i_center[1] < k_bbox[3]:
                        continue
                else:
                    continue

                # 3. 정규식 매칭 확인
                match = re.search(config['re'], item['text'])
                if not match: continue
                val = match.group(1)
                
                # 4. 면적 계산 및 후보 추가
                area = (i_bbox[2] - i_bbox[0]) * (i_bbox[3] - i_bbox[1])
                candidates.append((area, val))

            if candidates:
                # 면적이 가장 큰 후보(가장 굵거나 큰 텍스트)를 선택
                candidates.sort(key=lambda x: x[0], reverse=True)
                best_val = f"{candidates[0][1]} {config['unit']}".strip()
                matched_data[key] = best_val
                print(f"{key:<15} | {best_val:<15} | ✅ 성공")
            else:
                matched_data[key] = None
                print(f"{key:<15} | {'-':<15} | ⚠️ 값 미발견")

        print("-" * 60)
        print(f"총 소요 시간: {time.time() - start_time:.2f}초")
        print("=" * 60)
        
        return matched_data

if __name__ == "__main__":
    img_path = "/home/roh/workspace/ExplainMyBody/experiments/PaddleOCR/inbody/KakaoTalk_20260121_072053407.jpg"
    matcher = InBodyMatcher()
    result = matcher.extract_and_match(img_path)
    
    output_path = "/home/roh/workspace/ExplainMyBody/experiments/PaddleOCR/inbody_matched_summary.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장됨: {output_path}")
