"""
인바디 결과지 종합 매칭 - 텍스트 후처리 (OCR 제외)
"""

import os
import json
import re

import numpy as np
import time

class InBodyMatcher:
    def __init__(self):
        pass


    def extract_segmental_analysis(self, all_nodes, image_height, image_width):
        """
        부위별 근육분석 및 체지방분석 데이터 추출
        """
        result = {
            "부위별근육분석": {},
            "부위별체지방분석": {}
        }
        
        # 1. 제목 노드 찾기
        lean_title_node = None
        fat_title_node = None
        
        for node in all_nodes:
            if "부위별근육분석" in node['text'] or "Segmental Lean" in node['text']:
                lean_title_node = node
            elif "부위별체지방분석" in node['text'] or "Segmental Fat" in node['text']:
                fat_title_node = node
        
        # 2. 각 섹션별 데이터 추출
        body_parts = ["왼팔", "오른팔", "몸통", "왼다리", "오른다리"]
        evals = ["표준이하", "표준이상", "표준"]
        
        # 부위별근육분석 처리
        if lean_title_node:
            result["부위별근육분석"] = self.extract_section_data(
                lean_title_node, all_nodes, image_height, image_width, 
                body_parts, evals
            )
        
        # 부위별체지방분석 처리
        if fat_title_node:
            result["부위별체지방분석"] = self.extract_section_data(
                fat_title_node, all_nodes, image_height, image_width,
                body_parts, evals
            )
        
        return result


    def extract_section_data(self, title_node, all_nodes, image_height, image_width, 
                            body_parts, evals):
        print("실행됨")
        """
        특정 섹션의 데이터 추출
        """
        section_data = {}
        
        # ROI 설정 (제목 기준)
        title_x_min = title_node['bbox'][0]
        title_y_min = title_node['bbox'][1]
        
        roi_x_min = title_x_min
        roi_x_max = title_x_min + int(image_width * 0.38)
        roi_y_min = title_y_min + int(image_height * 0.02)
        roi_y_max = title_y_min + int(image_height * 0.13)
        
        # ROI 내의 평가 노드 필터링
        eval_nodes = []
        for node in all_nodes:
            node_x = node['center'][0]
            node_y = node['center'][1]
            
            if (roi_x_min <= node_x <= roi_x_max and 
                roi_y_min <= node_y <= roi_y_max and
                any(ev in node['text'] for ev in evals)):
                eval_nodes.append(node)
        
        # y좌표 기준 정렬
        eval_nodes = sorted(eval_nodes, key=lambda x: x['center'][1])
        
        # 각 부위별 매칭
        for i, part_name in enumerate(body_parts):
            if i < len(eval_nodes):
                eval_value = "알수없음"
                for ev in evals:
                    if ev in eval_nodes[i]['text']:
                        eval_value = ev
                        break
                section_data[part_name] = eval_value
            else:
                section_data[part_name] = "데이터없음"
        
        return section_data

    def extract_and_match(self, json_path):
        start_time = time.time()
        print(f"데이터 분석 및 보정 시작: {os.path.basename(json_path)}")
        
        # Load JSON data
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Mapping as requested
        # res['dt_polys'] -> data['polygon']
        # res['rec_texts'] -> data['texts']
        
        polygons = data.get("polygon", [])
        texts = data.get("texts", [])
        
        all_nodes = []
        
        # -----------------------------------------------------------
        # 아래 로직은 origincode.py에서 가져온 핵심 로직입니다.
        # -----------------------------------------------------------
        
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
        
        print("\n" + "="*60)
        print(f"{'항목명':<15} | {'추출된 값':<15} | {'상태'}")
        print("-" * 60)
        # vis_image = img.copy()
        # overlay = img.copy()

        for key, config in targets.items():
            yr_min, yr_max = config["yr"]
            # cv2.rectangle(overlay, (0, yr_min), (img.shape[1], yr_max), (230, 230, 230), -1) # ROI 영역 표시
            #or difflib.SequenceMatcher(None, key, n['text']).ratio() > 0.5
            candidates_k = [n for n in all_nodes if (yr_min - 20 <= n['center'][1] <= yr_max + 20) and 
                           (key in n['text'])]

            if not candidates_k:
                matched_data[key] = None
                print(f"{key:<15} | {'-':<15} | ⚠️ 값 미발견 (키워드 없음)")
                continue

            k_node = max(candidates_k, key=lambda x: x['conf'])
            # cv2.rectangle(vis_image, (k_node['bbox'][0], k_node['bbox'][1]), (k_node['bbox'][2], k_node['bbox'][3]), (255, 0, 0), 2)
            # cv2.putText(vis_image, key, (k_node['bbox'][0], k_node['bbox'][1]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

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
                        # cv2.rectangle(vis_image, (item['bbox'][0], item['bbox'][1]), (item['bbox'][2], item['bbox'][3]), (0, 165, 255), 2)
                        # cv2.putText(vis_image, "Scale", (item['bbox'][0], item['bbox'][1]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 165, 255), 1)
                        continue
                    
                    if "조절" not in key and (val == "0.0" or val == "0"): continue
                    candidates_v.append(((dy * 200) + (dx / 10), val, item))

            if candidates_v:
                candidates_v.sort(key=lambda x: x[0])
                final_val = candidates_v[0][1]
                matched_data[key] = final_val
                # v_node = candidates_v[0][2]
                print(f"{key:<15} | {final_val:<15} | ✅ 성공")
            else:
                matched_data[key] = None
                print(f"{key:<15} | {'-':<15} | ⚠️ 값 미발견 (값 없음)")





        # 사용 예시
        # image_height = 2400
        # image_width = 1800
        
        # TODO: 실제 이미지 크기를 알 수 없으므로, 좌표 기준으로 추정하거나 파라미터로 받아야 함
        # 여기서는 편의상 하드코딩
        image_height = 2400
        image_width = 1800
        
        segmental_results = self.extract_segmental_analysis(all_nodes, image_height, image_width)
        
        # 결과 병합
        matched_data.update(segmental_results)
        
        print("-" * 60)
        print(f"총 소요 시간: {time.time() - start_time:.2f}초")
        print(f"DEBUG: matched_data keys: {list(matched_data.keys())}")
        print("=" * 60)
        
        return matched_data


if __name__ == "__main__":
    # Test with output.json in the same directory
    current_dir = os.path.dirname(__file__)
    json_path = os.path.join(current_dir, "output.json")
    
    if os.path.exists(json_path):
        matcher = InBodyMatcher()
        result = matcher.extract_and_match(json_path)
        
        output_path = os.path.join(current_dir, "postprocessing_result.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n결과 저장됨: {output_path}")
    else:
        print(f"파일을 찾을 수 없습니다: {json_path}")
