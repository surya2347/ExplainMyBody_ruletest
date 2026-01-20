"""
## 분류 전략 클래스 모음 ##

================================
Classifier, adjuster, analyzer 등,
입력된 체성분 데이터로부터 stage1, stage2, stage3 체형을 분류하는 클래스 모음
또한 각 단계별 체형 분류때에 필요한 함수들을 포함

"""





# ============================================================================
# 1. 분류 전략 클래스 
# ============================================================================

import math
import constants as Constants

class BMIClassifier:
    """BMI 분류 전략"""
    
    @staticmethod
    def classify(bmi):
        """BMI 값을 카테고리로 분류"""
        try:
            bmi = float(bmi)
            
            if not math.isfinite(bmi):
                return round(bmi, 1), "알 수 없음"
            
            if bmi < Constants.BMIThreshold.UNDERWEIGHT:
                category = "저체중"
            elif bmi < Constants.BMIThreshold.NORMAL:
                category = "정상"
            elif bmi < Constants.BMIThreshold.OVERWEIGHT:
                category = "과체중"
            elif bmi < Constants.BMIThreshold.OBESE_1:
                category = "비만1단계"
            elif bmi < Constants.BMIThreshold.OBESE_2:
                category = "비만2단계"
            else:
                category = "고도비만"
            
            return round(bmi, 1), category
            
        except (TypeError, ValueError):
            return 0.0, "알 수 없음"


class BodyFatClassifier:
    """체지방률 분류 전략"""
    
    @staticmethod
    def classify(fat_rate):
        """체지방률을 카테고리로 분류"""
        try:
            fat_rate = float(fat_rate)
            
            if not math.isfinite(fat_rate):
                return "알 수 없음"
            
            if fat_rate < Constants.BodyFatThreshold.LOW:
                return "표준미만"
            elif fat_rate < Constants.BodyFatThreshold.NORMAL:
                return "표준"
            elif fat_rate < Constants.BodyFatThreshold.OVERWEIGHT:
                return "과체중"
            else:
                return "비만"
                
        except (TypeError, ValueError):
            return "알 수 없음"


class MuscleClassifier:
    """근육량 분류 전략"""
    
    @staticmethod
    def classify(smm, weight):
        """근육량/체중 비율로 근육 레벨 분류"""
        try:
            smm = float(smm)
            weight = float(weight)
            
            if weight == 0 or not math.isfinite(smm) or not math.isfinite(weight):
                return 0.0, "알 수 없음"
            
            ratio = smm / weight
            
            if not math.isfinite(ratio):
                return 0.0, "알 수 없음"
            
            if ratio >= Constants.MuscleRatioThreshold.VERY_HIGH:
                level = "근육 매우 많음"
            elif ratio >= Constants.MuscleRatioThreshold.HIGH:
                level = "근육 많음"
            elif ratio >= Constants.MuscleRatioThreshold.SUFFICIENT:
                level = "근육 충분"
            elif ratio >= Constants.MuscleRatioThreshold.NORMAL:
                level = "근육 보통"
            else:
                level = "근육 적음"
            
            return round(ratio, 3), level
            
        except (TypeError, ValueError, ZeroDivisionError):
            return 0.0, "알 수 없음"


# ============================================================================
# 2. Stage 1: 1차 체형 분류
# ============================================================================

class Stage1BodyTypeClassifier:
    """Stage 1: BMI + 체지방률 기반 체형 분류
        BMI와 체지방률을 기반으로 우선 분류.
        단, 비만 1단계 이상의 분류에서 골격근량을 사용해 근육형인지 단순 비만인지 판단"""
    
    @staticmethod
    def classify(bmi_cat, fat_cat, smm_cat=None):
        """
        ## 1차 체형 분류 로직
        """
        try:
            # 정상 체중인 경우
            if bmi_cat == "정상":
                return Stage1BodyTypeClassifier._classify_normal(fat_cat)
            
            # 저체중인 경우
            if bmi_cat == "저체중":
                return Stage1BodyTypeClassifier._classify_underweight(fat_cat)
            
            # 과체중인 경우
            if bmi_cat == "과체중":
                return Stage1BodyTypeClassifier._classify_overweight(fat_cat)
            
            # 비만 1단계인 경우
            if bmi_cat == "비만1단계":
                return Stage1BodyTypeClassifier._classify_obese1(fat_cat, smm_cat)
            
            # 비만 2단계인 경우
            if bmi_cat == "비만2단계":
                return Stage1BodyTypeClassifier._classify_obese2(fat_cat, smm_cat)
            
            # 고도비만인 경우
            if bmi_cat == "고도비만":
                return Stage1BodyTypeClassifier._classify_severe_obese(fat_cat, smm_cat)
            
            return "알 수 없음"
            
        except (TypeError, AttributeError):
            return "알 수 없음"
    
    @staticmethod
    def _classify_normal(fat_cat):
        """정상 체중 분류"""
        if fat_cat == "표준":
            return "표준형"
        elif fat_cat == "표준미만":
            return "마른형"
        else:
            return "마른비만형"
    
    @staticmethod
    def _classify_underweight(fat_cat):
        """저체중 분류"""
        if fat_cat in ["과체중", "비만"]:
            return "마른비만형"
        return "마른형"
    
    @staticmethod
    def _classify_overweight(fat_cat):
        """과체중 분류"""
        if fat_cat in ["과체중", "비만"]:
            return "비만형"
        return "근육형"
    
    @staticmethod
    def _classify_obese1(fat_cat, smm_cat):
        """비만 1단계 분류"""
        if fat_cat == "표준미만" and smm_cat in ["근육 매우 많음", "근육 많음", "근육 충분"]:
            return "근육형"
        return "비만형"
    
    @staticmethod
    def _classify_obese2(fat_cat, smm_cat):
        """비만 2단계 분류"""
        if fat_cat == "표준미만" and smm_cat in ["근육 매우 많음", "근육 많음"]:
            return "근육형"
        return "비만형"
    
    @staticmethod
    def _classify_severe_obese(fat_cat, smm_cat):
        """고도비만 분류"""
        if fat_cat == "표준미만" and smm_cat in ["근육 매우 많음", "근육 많음"]:
            return "근육형"
        return "고도비만형"


# ============================================================================
# 3. Stage 2: 근육량 보정
# ============================================================================

class Stage2MuscleAdjuster:
    """Stage 2: 근육량으로 체형 보정
        stage 1 에서 분류한 체형에 (골격근량 / 체중량)을 기반으로
        추가적으로 세분화된 체형 정보로 출력"""
    
    # 보정 테이블
    ADJUSTMENT_TABLE = {
        "마른형": {
            "근육 적음": "마른형",
            "근육 보통": "마른형",
            "근육 충분": "마른근육형",
            "근육 많음": "근육형",
            "근육 매우 많음": "근육형",
        },
        "표준형": {
            "근육 적음": "마른형",
            "근육 보통": "표준형",
            "근육 충분": "근육형",
            "근육 많음": "근육형",
            "근육 매우 많음": "근육형",
        },
        "근육형": {
            "근육 적음": "비만형",
            "근육 보통": "비만형",
            "근육 충분": "근육형",
            "근육 많음": "고근육체형",
            "근육 매우 많음": "고근육체형",
        },
        "비만형": {
            "근육 적음": "비만형",
            "근육 보통": "비만형",
            "근육 충분": "고근육체형",
            "근육 많음": "고근육체형",
            "근육 매우 많음": "고근육체형",
        },
        "고도비만형": {
            "근육 적음": "고도비만형",
            "근육 보통": "고도비만형",
            "근육 충분": "비만형",
            "근육 많음": "고근육체형",
            "근육 매우 많음": "고근육체형",
        },
        "마른비만형": {
            "근육 적음": "마른비만형",
            "근육 보통": "마른비만형",
            "근육 충분": "표준형",
            "근육 많음": "근육형",
            "근육 매우 많음": "고근육체형",
        }
    }
    
    @staticmethod
    def adjust(stage1_type, muscle_level):
        """근육 레벨(골격근량 / 체중량)으로 stage1의 체형 정보 보정"""
        try:
            adjusted_type = Stage2MuscleAdjuster.ADJUSTMENT_TABLE.get(
                stage1_type, {}
            ).get(muscle_level, stage1_type)
            
            return adjusted_type if adjusted_type else stage1_type
            
        except (TypeError, AttributeError, KeyError):
            return stage1_type
# ============================================================================
# 4. 부위별 분석 (근육/체지방)
# ============================================================================

class SegmentalAnalyzer:
    """부위별 근육/체지방 분석"""
    
    @staticmethod
    def is_numeric_data(seg_data):
        """데이터가 숫자 형식인지 확인"""
        try:
            if not isinstance(seg_data, dict):
                return False
            return all(isinstance(v, (int, float)) for v in seg_data.values())
        except (TypeError, AttributeError):
            return False
    
    @staticmethod
    def classify_part_level(value, reference, margin):
        """개별 부위의 발달도 분류"""
        try:
            value = float(value)
            reference = float(reference)
            margin = float(margin)
            
            if not all(math.isfinite(x) for x in [value, reference, margin]):
                return Constants.BodyPartLevel.NORMAL
            
            if reference == 0:
                return Constants.BodyPartLevel.NORMAL
            
            upper_threshold = reference * (1 + margin)
            lower_threshold = reference * (1 - margin)
            
            if value >= upper_threshold:
                return Constants.BodyPartLevel.ABOVE
            elif value <= lower_threshold:
                return Constants.BodyPartLevel.BELOW
            else:
                return Constants.BodyPartLevel.NORMAL
                
        except (TypeError, ValueError, ZeroDivisionError):
            return Constants.BodyPartLevel.NORMAL
    
    @staticmethod
    def calculate_development_ratio(parts, total):
        """부위별 발달도 비율 계산"""
        try:
            total = float(total)
            
            if total == 0 or not math.isfinite(total):
                return {k: 0.0 for k in parts.keys()}
            
            ratios = {}
            for key, value in parts.items():
                try:
                    value = float(value)
                    ratio = value / total if math.isfinite(value) else 0.0
                    ratios[key] = ratio
                except (TypeError, ValueError, ZeroDivisionError):
                    ratios[key] = 0.0
            
            return ratios
            
        except (TypeError, ValueError):
            return {k: 0.0 for k in parts.keys()}


class MuscleSegmentalAnalyzer(SegmentalAnalyzer):
    """근육 부위별 분석"""
    
    @staticmethod
    def classify(parts, total_smm, margin=Constants.ValidationLimits.DEFAULT_MARGIN):
        """부위별 근육 분류"""
        try:
            # 발달도 비율 계산
            dev = MuscleSegmentalAnalyzer.calculate_development_ratio(parts, total_smm)
            
            # 기준값 계산
            arm_ref = MuscleSegmentalAnalyzer._calculate_arm_reference(dev)
            leg_ref = MuscleSegmentalAnalyzer._calculate_leg_reference(dev)
            trunk_ref = MuscleSegmentalAnalyzer._calculate_trunk_reference(arm_ref, leg_ref)
            
            # 부위별 분류
            return {
                Constants.BodyPartKeys.LEFT_ARM: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.LEFT_ARM, 0), arm_ref, margin
                ),
                Constants.BodyPartKeys.RIGHT_ARM: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.RIGHT_ARM, 0), arm_ref, margin
                ),
                Constants.BodyPartKeys.TRUNK: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.TRUNK, 0), trunk_ref, margin
                ),
                Constants.BodyPartKeys.LEFT_LEG: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.LEFT_LEG, 0), leg_ref, margin
                ),
                Constants.BodyPartKeys.RIGHT_LEG: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.RIGHT_LEG, 0), leg_ref, margin
                ),
            }
            
        except (TypeError, KeyError, AttributeError):
            return MuscleSegmentalAnalyzer._get_default_classification()
    
    @staticmethod
    def _calculate_arm_reference(dev):
        """팔 기준값 계산"""
        try:
            left = dev.get(Constants.BodyPartKeys.LEFT_ARM, 0)
            right = dev.get(Constants.BodyPartKeys.RIGHT_ARM, 0)
            avg = (left + right) / 2.0
            return avg if math.isfinite(avg) else 0.0
        except (TypeError, ZeroDivisionError):
            return 0.0
    
    @staticmethod
    def _calculate_leg_reference(dev):
        """다리 기준값 계산"""
        try:
            left = dev.get(Constants.BodyPartKeys.LEFT_LEG, 0)
            right = dev.get(Constants.BodyPartKeys.RIGHT_LEG, 0)
            avg = (left + right) / 2.0
            return avg if math.isfinite(avg) else 0.0
        except (TypeError, ZeroDivisionError):
            return 0.0
    
    @staticmethod
    def _calculate_trunk_reference(arm_ref, leg_ref):
        """몸통 기준값 계산 (팔과 다리의 중간값)"""
        try:
            avg = (arm_ref + leg_ref) / 2.0
            return avg if math.isfinite(avg) else 0.0
        except (TypeError, ZeroDivisionError):
            return 0.0
    
    @staticmethod
    def _get_default_classification():
        """기본 분류값 반환"""
        return {
            Constants.BodyPartKeys.LEFT_ARM: Constants.BodyPartLevel.NORMAL,
            Constants.BodyPartKeys.RIGHT_ARM: Constants.BodyPartLevel.NORMAL,
            Constants.BodyPartKeys.TRUNK: Constants.BodyPartLevel.NORMAL,
            Constants.BodyPartKeys.LEFT_LEG: Constants.BodyPartLevel.NORMAL,
            Constants.BodyPartKeys.RIGHT_LEG: Constants.BodyPartLevel.NORMAL,
        }


class FatSegmentalAnalyzer(SegmentalAnalyzer):
    """체지방 부위별 분석"""
    
    @staticmethod
    def classify(fat_parts, total_fat, margin=Constants.ValidationLimits.DEFAULT_MARGIN):
        """부위별 체지방 분류"""
        try:
            # 발달도 비율 계산
            dev = FatSegmentalAnalyzer.calculate_development_ratio(fat_parts, total_fat)
            
            # 기준값 계산
            arm_ref = FatSegmentalAnalyzer._calculate_arm_reference(dev)
            leg_ref = FatSegmentalAnalyzer._calculate_leg_reference(dev)
            trunk_ref = FatSegmentalAnalyzer._calculate_trunk_reference(dev)
            
            # 부위별 분류
            return {
                Constants.BodyPartKeys.LEFT_ARM: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.LEFT_ARM, 0), arm_ref, margin
                ),
                Constants.BodyPartKeys.RIGHT_ARM: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.RIGHT_ARM, 0), arm_ref, margin
                ),
                Constants.BodyPartKeys.TRUNK: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.TRUNK, 0), trunk_ref, margin
                ),
                Constants.BodyPartKeys.LEFT_LEG: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.LEFT_LEG, 0), leg_ref, margin
                ),
                Constants.BodyPartKeys.RIGHT_LEG: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.RIGHT_LEG, 0), leg_ref, margin
                ),
            }
            
        except (TypeError, KeyError, AttributeError):
            return FatSegmentalAnalyzer._get_default_classification()
    
    @staticmethod
    def _calculate_arm_reference(dev):
        """팔 기준값 계산"""
        try:
            left = dev.get(Constants.BodyPartKeys.LEFT_ARM, 0)
            right = dev.get(Constants.BodyPartKeys.RIGHT_ARM, 0)
            avg = (left + right) / 2.0
            return avg if math.isfinite(avg) else 0.0
        except (TypeError, ZeroDivisionError):
            return 0.0
    
    @staticmethod
    def _calculate_leg_reference(dev):
        """다리 기준값 계산"""
        try:
            left = dev.get(Constants.BodyPartKeys.LEFT_LEG, 0)
            right = dev.get(Constants.BodyPartKeys.RIGHT_LEG, 0)
            avg = (left + right) / 2.0
            return avg if math.isfinite(avg) else 0.0
        except (TypeError, ZeroDivisionError):
            return 0.0
    
    @staticmethod
    def _calculate_trunk_reference(dev):
        """몸통 기준값 계산 (체지방은 자기 자신 기준)"""
        try:
            trunk = dev.get(Constants.BodyPartKeys.TRUNK, 0)
            return trunk if math.isfinite(trunk) else 0.0
        except TypeError:
            return 0.0
    
    @staticmethod
    def _get_default_classification():
        """기본 분류값 반환"""
        return {
            Constants.BodyPartKeys.LEFT_ARM: Constants.BodyPartLevel.NORMAL,
            Constants.BodyPartKeys.RIGHT_ARM: Constants.BodyPartLevel.NORMAL,
            Constants.BodyPartKeys.TRUNK: Constants.BodyPartLevel.NORMAL,
            Constants.BodyPartKeys.LEFT_LEG: Constants.BodyPartLevel.NORMAL,
            Constants.BodyPartKeys.RIGHT_LEG: Constants.BodyPartLevel.NORMAL,
        }


# ============================================================================
# 5. 정규화 (Normalization)
# ============================================================================

class DataNormalizer:
    """데이터 정규화 처리"""
    
    @staticmethod
    def normalize_muscle_segment(muscle_input, total_smm, margin=Constants.ValidationLimits.DEFAULT_MARGIN):
        """근육 데이터 정규화 (숫자 → 표준/표준이상/표준미만)"""
        try:
            # 이미 텍스트 형태인 경우 그대로 반환
            if not SegmentalAnalyzer.is_numeric_data(muscle_input):
                return muscle_input
            
            # 숫자 형태인 경우 분류 수행
            return MuscleSegmentalAnalyzer.classify(muscle_input, total_smm, margin)
            
        except (TypeError, AttributeError):
            return muscle_input
    
    @staticmethod
    def normalize_fat_segment(fat_input, total_fat, margin=Constants.ValidationLimits.DEFAULT_MARGIN):
        """체지방 데이터 정규화 (숫자 → 표준/표준이상/표준미만)"""
        try:
            # 이미 텍스트 형태인 경우 그대로 반환
            if not SegmentalAnalyzer.is_numeric_data(fat_input):
                return fat_input
            
            # 숫자 형태인 경우 분류 수행
            return FatSegmentalAnalyzer.classify(fat_input, total_fat, margin)
            
        except (TypeError, AttributeError):
            return fat_input


# ============================================================================
# 6. Stage 3: 상하체 밸런스 분석
# ============================================================================

class Stage3BalanceAnalyzer:
    """Stage 3: 상하체 밸런스 분석"""
    
    @staticmethod
    def analyze_distribution(seg_data):
        """부위별 데이터에서 상체/하체 분포 판정"""
        try:
            arm_high_count = Stage3BalanceAnalyzer._count_high_arms(seg_data)
            leg_high_count = Stage3BalanceAnalyzer._count_high_legs(seg_data)
            
            if leg_high_count >= 2 and arm_high_count < 2:
                return "하체"
            elif arm_high_count >= 2 and leg_high_count < 2:
                return "상체"
            else:
                return "균형"
                
        except (TypeError, KeyError, AttributeError):
            return "균형"
    
    @staticmethod
    def _count_high_arms(seg_data):
        """팔 부위에서 '표준이상' 개수 카운트"""
        try:
            count = 0
            if seg_data.get(Constants.BodyPartKeys.RIGHT_ARM) == Constants.BodyPartLevel.ABOVE:
                count += 1
            if seg_data.get(Constants.BodyPartKeys.LEFT_ARM) == Constants.BodyPartLevel.ABOVE:
                count += 1
            return count
        except (TypeError, AttributeError):
            return 0
    
    @staticmethod
    def _count_high_legs(seg_data):
        """다리 부위에서 '표준이상' 개수 카운트"""
        try:
            count = 0
            if seg_data.get(Constants.BodyPartKeys.RIGHT_LEG) == Constants.BodyPartLevel.ABOVE:
                count += 1
            if seg_data.get(Constants.BodyPartKeys.LEFT_LEG) == Constants.BodyPartLevel.ABOVE:
                count += 1
            return count
        except (TypeError, AttributeError):
            return 0
    
    @staticmethod
    def classify(muscle_seg, fat_seg=None):
        """상하체 밸런스 최종 분류"""
        try:
            muscle_dist = Stage3BalanceAnalyzer.analyze_distribution(muscle_seg)
            
            # 체지방 데이터가 없는 경우
            if fat_seg is None:
                return Stage3BalanceAnalyzer._classify_by_muscle_only(muscle_dist)
            
            # 체지방 데이터가 있는 경우
            fat_dist = Stage3BalanceAnalyzer.analyze_distribution(fat_seg)
            return Stage3BalanceAnalyzer._classify_with_fat(muscle_dist, fat_dist)
            
        except (TypeError, AttributeError):
            return "표준형"
    
    @staticmethod
    def _classify_by_muscle_only(muscle_dist):
        """근육 데이터만으로 분류"""
        if muscle_dist == "하체":
            return "하체발달형"
        elif muscle_dist == "상체":
            return "상체발달형"
        else:
            return "표준형"
    
    @staticmethod
    def _classify_with_fat(muscle_dist, fat_dist):
        """근육 + 체지방 데이터로 분류"""
        # 체지방 분포가 우선
        if fat_dist == "하체":
            return "하체비만형"
        elif fat_dist == "상체":
            return "상체비만형"
        
        # 체지방이 균형이면 근육 분포 확인
        if muscle_dist == "하체":
            return "하체발달형"
        elif muscle_dist == "상체":
            return "상체발달형"
        else:
            return "표준형"
