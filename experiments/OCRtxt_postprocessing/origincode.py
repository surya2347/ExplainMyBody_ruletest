"""
인바디 결과지 초정밀 매칭 - 14차 시각화 강화판 (Filter Visibility + Reason Highlighting)
"""

import os
import cv2
import json
import re
import numpy as np
import time
import difflib
from paddleocr import PaddleOCR

class InBodyMatcher:
    def __init__(self):
        os.environ['FLAGS_use_mkldnn'] = '0'
        os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
        # 한국어는 V5가 최신 고성능 표준이므로 기본 모델(V5)을 사용합니다.
        self.ocr = PaddleOCR(lang='korean', use_textline_orientation=True)
        
        self.correction_map = {
            "척정체중": "적정체중", "정체중": "적정체중", "체지방륨": "체지방률", "체지방율": "체지방률",
            "골격극량": "골격근량", "극근량": "골격근량", "무기실": "무기질", "보부지방률": "복부지방률",
            "부지방률": "복부지방률", "내장지방레빌": "내장지방레벨", "제지방륨": "제지방량"
        }

    def extract_and_match(self, image_path, output_vis_path="inbody_matching_vis.jpg"):
        src_img = cv2.imread(image_path)
        if src_img is None: return {}
        target_h = 2400
        img = cv2.resize(src_img, (int(src_img.shape[1] * (target_h / src_img.shape[0])), target_h), interpolation=cv2.INTER_LANCZOS4)
        cv2.imwrite("temp_standard_image.jpg", img)

        result = self.ocr.predict(input="temp_standard_image.jpg")
        all_nodes = []
        if result:
            for res in result:
                # for poly, text, conf in zip(res['dt_polys'], res['rec_texts'], res.get('rec_scores', [])):
                for poly, text in zip(res['dt_polys'], res['rec_texts']):
                    pts = np.array(poly)
                    all_nodes.append({
                        'text': text.strip().replace(" ", "").replace("|", ""),
                        'bbox': [int(pts.min(axis=0)[0]), int(pts.min(axis=0)[1]), int(pts.max(axis=0)[0]), int(pts.max(axis=0)[1])],
                        'center': [(pts.min(axis=0)[0] + pts.max(axis=0)[0]) / 2, (pts.min(axis=0)[1] + pts.max(axis=0)[1]) / 2],
                        # 'conf': float(conf)
                    })

        # [ROI 정밀 재조정] V5 모델 성능에 맞춰 범위를 다시 타이트하게 설정 (인접 행 혼입 방지)
        targets = {
            "신장": {"re": r"(\d{3})", "yr": [130, 210], "dir": "down"},
            "연령": {"re": r"(\d{2})", "yr": [130, 210], "dir": "down"},
            "성별": {"re": r"(남성|여성|남|여)$", "yr": [130, 210], "dir": "down"},
            "체수분": {"re": r"(\d+\.\d+)", "yr": [320, 370], "dir": "right"},
            "단백질": {"re": r"(\d+\.\d+)", "yr": [380, 430], "dir": "right"},
            "무기질": {"re": r"(\d+\.\d+)", "yr": [440, 480], "dir": "right"},
            "체지방": {"re": r"(\d+\.\d+)", "yr": [490, 540], "dir": "right"},
            
            # 머슬-팻 분석: 범위를 매우 좁게 설정하여 행 섞임 방지
            "체중": {"re": r"(\d+\.\d+)", "yr": [760, 810], "dir": "right"},    # 77.7
            "골격근량": {"re": r"(\d+\.\d+)", "yr": [830, 885], "dir": "right"}, # 32.5
            "체지방량": {"re": r"(\d+\.\d+)", "yr": [900, 960], "dir": "right"}, # 20.6
            
            "적정체중": {"re": r"(\d+\.\d+)", "yr": [560, 610], "dir": "right"},
            "체중조절": {"re": r"([-+]\d+\.\d+)", "yr": [600, 650], "dir": "right"},
            "지방조절": {"re": r"([-+]\d+\.\d+)", "yr": [640, 690], "dir": "right"},
            "근육조절": {"re": r"0.0|(\d+\.\d+)", "yr": [680, 725], "dir": "right"},
            
            "복부지방률": {"re": r"(\d\.\d{2})", "yr": [900, 1020], "dir": "down"}, 
            "내장지방레벨": {"re": r"(\d+)", "yr": [1000, 1150], "dir": "down"},
            
            "BMI": {"re": r"(\d+\.\d+)", "yr": [1120, 1180], "dir": "right"}, 
            "체지방률": {"re": r"(\d+\.\d+)", "yr": [1190, 1260], "dir": "right"}, 
            
            "제지방량": {"re": r"(\d+\.\d+)", "yr": [1160, 1195], "dir": "right"},
            "기초대사량": {"re": r"(\d{4})", "yr": [1200, 1235], "dir": "right"},
            "비만도": {"re": r"(\d+)", "yr": [1235, 1275], "dir": "right"},
            "권장섭취열량": {"re": r"(\d{4})", "yr": [1270, 1320], "dir": "right"},
        }

        # 눈금값 사전 (필터링 대상)
        scale_vals = set(['0.0', '5.0', '10.0', '15.0', '16.0', '18.5', '20.0', '21.0', '22.0', '23.0', '25.0', '30.0', '35.0', '40.0', '45.0', '50.0', '55.0', '70', '80', '85', '100', '115', '120', '130', '140', '145', '150', '160', '170', '175', '190', '205', '220', '280', '340', '400', '460', '520', '00'])

        matched_data = {}
        vis_image = img.copy()
        overlay = img.copy()

        for key, config in targets.items():
            yr_min, yr_max = config["yr"]
            cv2.rectangle(overlay, (0, yr_min), (img.shape[1], yr_max), (230, 230, 230), -1) # ROI 영역 표시
            
            candidates_k = [n for n in all_nodes if (yr_min - 20 <= n['center'][1] <= yr_max + 20) and 
                           (key in self.correction_map.get(n['text'], n['text']) or difflib.SequenceMatcher(None, key, self.correction_map.get(n['text'], n['text'])).ratio() > 0.5)]

            if not candidates_k:
                matched_data[key] = None; continue

            k_node = max(candidates_k, key=lambda x: x['conf'])
            cv2.rectangle(vis_image, (k_node['bbox'][0], k_node['bbox'][1]), (k_node['bbox'][2], k_node['bbox'][3]), (255, 0, 0), 2)
            cv2.putText(vis_image, key, (k_node['bbox'][0], k_node['bbox'][1]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

            candidates_v = []
            for item in all_nodes:
                if item == k_node: continue
                match = re.search(config['re'], item['text'])
                if not match: continue
                val = match.group(0) if "조절" in key else match.group(1)
                
                # 가중치 및 필터 로직 시각화 준비
                i_center = item['center']
                dx = i_center[0] - k_node['bbox'][2] if config.get("dir", "right") == "right" else abs(i_center[0] - k_node['center'][0])
                dy = abs(i_center[1] - k_node['center'][1])
                
                # 수평 라인 및 ROI 체크
                in_roi = (yr_min - 10 <= i_center[1] <= yr_max + 50)
                is_right_dir = (config.get("dir", "right") == "right" and 0 < dx < 900 and dy < 60)
                is_down_dir = (config.get("dir") == "down" and 0 < (item['center'][1] - k_node['bbox'][3]) < 350 and dx < 120)
                
                if in_roi and (is_right_dir or is_down_dir):
                    if item['text'] in scale_vals:
                        # [시각화] 필터링된 눈금값은 주황색으로 표시
                        cv2.rectangle(vis_image, (item['bbox'][0], item['bbox'][1]), (item['bbox'][2], item['bbox'][3]), (0, 165, 255), 2)
                        cv2.putText(vis_image, "Scale", (item['bbox'][0], item['bbox'][1]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 165, 255), 1)
                        continue
                    
                    if "조절" not in key and (val == "0.0" or val == "0"): continue
                    candidates_v.append(((dy * 200) + (dx / 10), val, item))

            if candidates_v:
                candidates_v.sort(key=lambda x: x[0])
                matched_data[key] = candidates_v[0][1]
                v_node = candidates_v[0][2]
                # [시각화] 최종 매칭된 수치는 녹색으로 표시
                cv2.rectangle(vis_image, (v_node['bbox'][0], v_node['bbox'][1]), (v_node['bbox'][2], v_node['bbox'][3]), (0, 255, 0), 3)
                cv2.putText(vis_image, "Value", (v_node['bbox'][0], v_node['bbox'][1]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # 부위별 분석 시각화
        evals = ["표준이하", "표준이상", "표준"]
        body_parts = ["왼쪽팔", "오른쪽팔", "복부", "왼쪽하체", "오른쪽하체"]
        eval_nodes = sorted([n for n in all_nodes if any(ev in n['text'] for ev in evals) and (1450 <= n['center'][1] <= 1800)], key=lambda x: x['center'][1])
        for i, part in enumerate(body_parts):
            if i*2+1 < len(eval_nodes):
                row_nodes = sorted(eval_nodes[i*2:i*2+2], key=lambda x: x['center'][0])
                matched_data[f"{part} 근육"] = next((ev for ev in evals if ev in row_nodes[0]['text']), "알수없음")
                matched_data[f"{part} 체지방"] = next((ev for ev in evals if ev in row_nodes[1]['text']), "알수없음")
                cv2.rectangle(vis_image, (row_nodes[0]['bbox'][0], row_nodes[0]['bbox'][1]), (row_nodes[0]['bbox'][2], row_nodes[0]['bbox'][3]), (255, 128, 0), 2)
                cv2.rectangle(vis_image, (row_nodes[1]['bbox'][0], row_nodes[1]['bbox'][1]), (row_nodes[1]['bbox'][2], row_nodes[1]['bbox'][3]), (0, 128, 255), 2)

        vis_image = cv2.addWeighted(overlay, 0.2, vis_image, 0.8, 0)
        cv2.imwrite(output_vis_path, vis_image)
        return matched_data

if __name__ == "__main__":
    img_path = "/home/roh/workspace/ExplainMyBody/experiments/PaddleOCR/inbody/KakaoTalk_20260121_182041251.jpg"
    result = InBodyMatcher().extract_and_match(img_path)
    with open("/home/roh/workspace/ExplainMyBody/experiments/PaddleOCR/inbody_matched_final.json", 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*50)
    print(f"{'항목':<15} | {'결과'}")
    print("-" * 50)
    for key, val in result.items():
        print(f"{key:<15} | {val if val else '미검출'}")
    print("="*50)
    print(f"\n[시각화 고도화] 이미지에 'Scale'(눈금)과 'Value'(실제값) 구분 표시를 추가했습니다.")
