"""
## 통합 분석 파이프라인 (Facade Pattern) ##

============================================

체성분 분석의 전체적인 흐름을 추상화하여 통합 분석 파이프라인을 구현합니다.


"""

# ============================================================================
# 통합 분석 파이프라인 (Facade Pattern)
# ============================================================================



from classifiers import (
    BMIClassifier,
    BodyFatClassifier,
    MuscleClassifier,
    Stage1BodyTypeClassifier,
    Stage2MuscleAdjuster,
    DataNormalizer,
    Stage3BalanceAnalyzer
)
from constants import ValidationLimits, BodyCompositionData



class BodyCompositionAnalyzer:
    """체성분 분석 통합 파이프라인"""
    
    def __init__(self, margin=ValidationLimits.DEFAULT_MARGIN):
        self.margin = margin
    
    @staticmethod
    def _get_value(data, key):
        """딕셔너리 또는 객체에서 값을 가져오는 헬퍼 함수"""
        if isinstance(data, dict):
            return data.get(key)
        else:
            return getattr(data, key, None)
    
    @staticmethod
    def _get_total_fat(data):
        """총 체지방량 계산"""
        if isinstance(data, dict):
            # 딕셔너리인 경우 직접 계산
            return data["weight_kg"] * data["fat_rate"] / 100.0
        else:
            # BodyCompositionData 객체인 경우 메서드 호출
            return data.get_total_fat()

    def analyze_full_pipeline(self, data):
        """전체 파이프라인 분석 (Stage 1 + 2 + 3)
        
        Args:
            data: BodyCompositionData 객체 또는 딕셔너리
                  딕셔너리인 경우 자동으로 BodyCompositionData 객체로 변환됩니다.
        
        Returns:
            dict: 분석 결과
        """
        try:
            # 딕셔너리인 경우 BodyCompositionData 객체로 변환
            if isinstance(data, dict):
                data = BodyCompositionData.from_dict(data)
            
            # Stage 1 + 2: 체형 분류 및 근육 보정
            # BMI 분류
            bmi_value, bmi_cat = BMIClassifier.classify(self._get_value(data, "bmi"))
            
            # 체지방률 분류
            fat_cat = BodyFatClassifier.classify(self._get_value(data, "fat_rate"))
            
            # 근육량 분류
            smm_ratio, muscle_level = MuscleClassifier.classify(
                self._get_value(data, "smm"), 
                self._get_value(data, "weight_kg")
            )
            
            # Stage 1: 1차 체형 분류
            stage1_type = Stage1BodyTypeClassifier.classify(bmi_cat, fat_cat, muscle_level)
            
            # Stage 2: 근육량 보정
            stage2_type = Stage2MuscleAdjuster.adjust(stage1_type, muscle_level)
            
            # Stage 1+2 결과 저장
            stage12_result = {
                "bmi": bmi_value,
                "bmi_category": bmi_cat,
                "fat_category": fat_cat,
                "smm_ratio": smm_ratio,
                "muscle_level": muscle_level,
                "stage1_type": stage1_type,
                "stage2_type": stage2_type
            }
            
            # 근육 데이터 정규화
            muscle_seg = DataNormalizer.normalize_muscle_segment(
                self._get_value(data, "muscle_seg"),
                self._get_value(data, "smm"),
                self.margin
            )
            
            # 체지방 데이터 정규화
            fat_seg = None
            if self._get_value(data, "fat_seg") is not None:
                # 총 체지방량 계산
                total_fat = self._get_total_fat(data)
                fat_seg = DataNormalizer.normalize_fat_segment(
                    self._get_value(data, "fat_seg"),
                    total_fat,
                    self.margin
                )
            
            # Stage 3: 상하체 밸런스 분석
            stage3_type = Stage3BalanceAnalyzer.classify(muscle_seg, fat_seg)
            
            return {
                "basic_info": {
                    "sex": self._get_value(data, "sex"),
                    "age": self._get_value(data, "age"),
                    "height_cm": self._get_value(data, "height_cm"),
                    "weight_kg": self._get_value(data, "weight_kg")
                },
                "stage1_2": stage12_result,
                "muscle_seg": muscle_seg,
                "fat_seg": fat_seg,
                "stage3": stage3_type
            }
            
        except Exception as e:
            # 디버깅을 위한 에러 출력
            print(f"[ERROR] analyze_full_pipeline 실패: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "basic_info": {
                    "sex": self._get_value(data, "sex") or "N/A",
                    "age": self._get_value(data, "age") or "N/A",
                    "height_cm": self._get_value(data, "height_cm") or "N/A",
                    "weight_kg": self._get_value(data, "weight_kg") or "N/A"
                },
                "stage1_2": {
                    "bmi": "N/A",
                    "bmi_category": "N/A",
                    "fat_category": "N/A",
                    "smm_ratio": "N/A",
                    "muscle_level": "N/A",
                    "stage1_type": "N/A",
                    "stage2_type": "N/A"
                },
                "muscle_seg": None,
                "fat_seg": None,
                "stage3": "알 수 없음"
            }
