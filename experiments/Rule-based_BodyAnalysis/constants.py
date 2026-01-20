"""
## 상수, 데이터 클래스 정의 ##

================================
인바디 정보를 분석하기 위한 상수와 데이터 클래스 정의

"""


# ============================================================================
# 1. 상수 정의 (Constants)
# ============================================================================

import math

class BMIThreshold:
    """BMI 분류 임계값"""
    UNDERWEIGHT = 18.5
    NORMAL = 23.0
    OVERWEIGHT = 24.9
    OBESE_1 = 29.9
    OBESE_2 = 34.9


class BodyFatThreshold:
    """체지방률 분류 임계값"""
    LOW = 10.0
    NORMAL = 20.0
    OVERWEIGHT = 24.0


class MuscleRatioThreshold:
    """근육량/체중 비율 임계값"""
    VERY_HIGH = 0.55
    HIGH = 0.50
    SUFFICIENT = 0.45
    NORMAL = 0.40


class ValidationLimits:
    """검증 한계값"""
    MIN_WEIGHT = 1.0
    MAX_WEIGHT = 500.0
    MIN_BMI = 10.0
    MAX_BMI = 100.0
    MIN_FAT_RATE = 0.0
    MAX_FAT_RATE = 100.0
    MIN_MUSCLE = 0.0
    DEFAULT_MARGIN = 0.10


class BodyPartLevel:
    """부위별 발달도 분류"""
    ABOVE = "표준이상"
    NORMAL = "표준"
    BELOW = "표준미만"


class BodyPartKeys:
    """부위 키 상수"""
    LEFT_ARM = "왼팔"
    RIGHT_ARM = "오른팔"
    TRUNK = "몸통"
    LEFT_LEG = "왼다리"
    RIGHT_LEG = "오른다리"

# ============================================================================
# 2. 데이터 타입 클래스 (Data Classes)
# ============================================================================

class BodyCompositionData:
    """체성분 데이터를 통합 관리하는 클래스"""
    
    def __init__(self):
        self.sex = None
        self.age = None
        self.height_cm = None
        self.weight_kg = None
        self.bmi = None
        self.fat_rate = None
        self.smm = None
        self.muscle_seg = None
        self.fat_seg = None
    
    @classmethod
    def from_dict(cls, data_dict):
        """딕셔너리를 BodyCompositionData 객체로 변환
        
        Args:
            data_dict: 체성분 데이터가 담긴 딕셔너리
            
        Returns:
            BodyCompositionData: 변환된 객체
            
        Example:
            >>> data_dict = {
            ...     "sex": "남성",
            ...     "age": 25,
            ...     "height_cm": 175,
            ...     "weight_kg": 70,
            ...     "bmi": 23.1,
            ...     "fat_rate": 15.2,
            ...     "smm": 25.4,
            ...     "muscle_seg": {...},
            ...     "fat_seg": {...}
            ... }
            >>> data = BodyCompositionData.from_dict(data_dict)
        """
        obj = cls()
        
        # 기본 정보 설정
        if all(k in data_dict for k in ["sex", "age", "height_cm", "weight_kg"]):
            obj.set_basic_info(
                sex=data_dict["sex"],
                age=data_dict["age"],
                height_cm=data_dict["height_cm"],
                weight_kg=data_dict["weight_kg"]
            )
        
        # 체성분 정보 설정
        if all(k in data_dict for k in ["bmi", "fat_rate", "smm"]):
            obj.set_composition(
                bmi=data_dict["bmi"],
                fat_rate=data_dict["fat_rate"],
                smm=data_dict["smm"]
            )
        
        # 부위별 데이터 설정
        if "muscle_seg" in data_dict:
            obj.set_segmental_data(
                muscle_seg=data_dict.get("muscle_seg"),
                fat_seg=data_dict.get("fat_seg")
            )
        
        return obj
    
    def set_basic_info(self, sex, age, height_cm, weight_kg):
        """기본 정보 설정"""
        self.sex = sex
        self.age = age
        self.height_cm = height_cm
        self.weight_kg = weight_kg
        return self
    
    def set_composition(self, bmi, fat_rate, smm):
        """체성분 정보 설정"""
        self.bmi = bmi
        self.fat_rate = fat_rate
        self.smm = smm
        return self
    
    def set_segmental_data(self, muscle_seg, fat_seg=None):
        """부위별 데이터 설정"""
        self.muscle_seg = muscle_seg
        self.fat_seg = fat_seg
        return self
    
    def get_total_fat(self):
        """총 체지방량 계산"""
        try:
            total_fat = self.weight_kg * self.fat_rate / 100.0
            if not math.isfinite(total_fat) or total_fat < 0:
                return 0.0
            return total_fat
        except (TypeError, ZeroDivisionError):
            return 0.0
