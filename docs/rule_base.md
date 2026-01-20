# Rule-based Body Analysis 개발 문서

## 📋 프로젝트 개요

### 프로젝트 목적
인바디(InBody) 체성분 데이터를 기반으로 사용자의 체형을 **규칙 기반(Rule-based)** 방식으로 분석하는 시스템입니다. 머신러닝이나 AI 모델 없이 순수하게 의학적/생리학적 기준과 임계값을 사용하여 체형을 분류합니다.

### 주요 기능
- **3단계 체형 분류 시스템**
  - Stage 1: BMI + 체지방률 기반 1차 체형 분류
  - Stage 2: 근육량 보정을 통한 2차 체형 분류
  - Stage 3: 상하체 밸런스 분석
- **부위별 근육/체지방 분석** (왼팔, 오른팔, 몸통, 왼다리, 오른다리)
- **유연한 데이터 입력** (딕셔너리 또는 객체 형태 모두 지원)

---

## 🏗️ 시스템 아키텍처

### 전체 구조
```
Rule-based_BodyAnalysis/
├── constants.py          # 상수 및 데이터 클래스 정의
├── classifiers.py        # 분류 전략 클래스 모음
├── integration.py        # 통합 분석 파이프라인 (Facade Pattern)
├── main_test.py          # 메인 실행 파일
└── utils_test.py         # 결과 출력 유틸리티
```

### 디자인 패턴
- **Strategy Pattern**: 각 분류 로직을 독립적인 클래스로 분리
- **Facade Pattern**: 복잡한 분석 과정을 단일 인터페이스로 통합
- **Builder Pattern**: BodyCompositionData 클래스의 메서드 체이닝

---

## 📥 Input 데이터 형식

### 1. 딕셔너리 형태 (권장)
```python
input_data = {
    # 기본 정보
    "sex": "남성",           # 성별
    "age": 25,               # 나이
    "height_cm": 175,        # 키 (cm)
    "weight_kg": 70,         # 체중 (kg)
    
    # 체성분 정보
    "bmi": 23.1,             # BMI 지수
    "fat_rate": 15.2,        # 체지방률 (%)
    "smm": 25.4,             # 골격근량 (kg)
    
    # 부위별 근육량 (kg)
    "muscle_seg": {
        "왼팔": 2.1,
        "오른팔": 2.2,
        "몸통": 10.3,
        "왼다리": 12.4,
        "오른다리": 12.5
    },
    
    # 부위별 체지방량 (kg) - 선택사항
    "fat_seg": {
        "왼팔": 1.1,
        "오른팔": 1.2,
        "몸통": 4.3,
        "왼다리": 6.4,
        "오른다리": 6.5
    }
}
```

### 2. BodyCompositionData 객체 형태
```python
from constants import BodyCompositionData

data = BodyCompositionData()
data.set_basic_info("남성", 25, 175, 70)
data.set_composition(23.1, 15.2, 25.4)
data.set_segmental_data(muscle_seg={...}, fat_seg={...})
```

> **Note**: 딕셔너리로 입력해도 내부적으로 자동으로 `BodyCompositionData` 객체로 변환됩니다.

---

## 📤 Output 데이터 형식

### 분석 결과 구조
```python
analysis_result = {
    # 기본 정보
    "basic_info": {
        "sex": "남성",
        "age": 25,
        "height_cm": 175,
        "weight_kg": 70
    },
    
    # Stage 1 + 2 결과
    "stage1_2": {
        "bmi": 23.1,                    # BMI 값
        "bmi_category": "과체중",        # BMI 분류
        "fat_category": "표준",          # 체지방 분류
        "smm_ratio": 0.363,             # 근육량/체중 비율
        "muscle_level": "근육 적음",     # 근육 레벨
        "stage1_type": "근육형",         # 1차 체형
        "stage2_type": "비만형"          # 2차 체형 (근육 보정)
    },
    
    # 부위별 근육 분석
    "muscle_seg": {
        "왼팔": "표준",
        "오른팔": "표준",
        "몸통": "표준이상",
        "왼다리": "표준",
        "오른다리": "표준"
    },
    
    # 부위별 체지방 분석
    "fat_seg": {
        "왼팔": "표준",
        "오른팔": "표준",
        "몸통": "표준",
        "왼다리": "표준",
        "오른다리": "표준"
    },
    
    # Stage 3 결과
    "stage3": "표준형"  # 상하체 밸런스 분석 결과
}
```

---

## ⚙️ 시스템 메커니즘

### 1. 데이터 흐름
```
입력 데이터 (딕셔너리/객체)
    ↓
[자동 변환] → BodyCompositionData 객체
    ↓
[Stage 1] BMI + 체지방률 분류
    ↓
[Stage 2] 근육량 보정
    ↓
[부위별 분석] 근육/체지방 정규화
    ↓
[Stage 3] 상하체 밸런스 분석
    ↓
분석 결과 (딕셔너리)
```

### 2. 핵심 모듈 설명

#### 📄 `constants.py`
**역할**: 시스템 전반에 사용되는 상수와 데이터 클래스 정의

**주요 클래스**:
- `BMIThreshold`: BMI 분류 기준값 (저체중 18.5, 정상 23.0, 과체중 24.9 등)
- `BodyFatThreshold`: 체지방률 분류 기준값
- `MuscleRatioThreshold`: 근육량/체중 비율 기준값
- `ValidationLimits`: 데이터 검증 한계값 및 기본 마진(0.10)
- `BodyPartLevel`: 부위별 발달도 분류 ("표준이상", "표준", "표준미만")
- `BodyPartKeys`: 부위 키 상수 ("왼팔", "오른팔", "몸통", "왼다리", "오른다리")
- **`BodyCompositionData`**: 체성분 데이터 관리 클래스
  - `from_dict()`: 딕셔너리 → 객체 변환 (핵심 기능!)
  - `get_total_fat()`: 총 체지방량 계산

#### 📄 `classifiers.py`
**역할**: 각 단계별 분류 전략 클래스 모음

**주요 클래스**:

1. **기본 분류기**
   - `BMIClassifier`: BMI 값을 카테고리로 분류
   - `BodyFatClassifier`: 체지방률을 카테고리로 분류
   - `MuscleClassifier`: 근육량/체중 비율로 근육 레벨 분류

2. **Stage 1: 1차 체형 분류**
   - `Stage1BodyTypeClassifier`: BMI + 체지방률 기반 체형 분류
   - 분류 결과: "마른형", "표준형", "근육형", "비만형", "고도비만형", "마른비만형"

3. **Stage 2: 근육량 보정**
   - `Stage2MuscleAdjuster`: 근육 레벨로 Stage1 체형 보정
   - 보정 테이블을 사용하여 세분화된 체형 출력
   - 예: "마른형" + "근육 충분" → "마른근육형"

4. **부위별 분석**
   - `SegmentalAnalyzer`: 부위별 분석 기본 클래스
   - `MuscleSegmentalAnalyzer`: 부위별 근육 분석
   - `FatSegmentalAnalyzer`: 부위별 체지방 분석
   - `DataNormalizer`: 숫자 데이터를 텍스트 분류로 정규화

5. **Stage 3: 상하체 밸런스**
   - `Stage3BalanceAnalyzer`: 근육/체지방 분포로 상하체 밸런스 분석
   - 분류 결과: "상체발달형", "하체발달형", "상체비만형", "하체비만형", "표준형"

#### 📄 `integration.py`
**역할**: 전체 분석 파이프라인 통합 (Facade Pattern)

**주요 클래스**:
- `BodyCompositionAnalyzer`: 통합 분석 파이프라인
  - `_get_value()`: 딕셔너리/객체 통합 접근 헬퍼
  - `_get_total_fat()`: 총 체지방량 계산 헬퍼
  - **`analyze_full_pipeline()`**: 전체 분석 실행 (메인 메서드)

**분석 프로세스**:
1. 입력 데이터 자동 변환 (딕셔너리 → 객체)
2. Stage 1+2 분석 (체형 분류 및 근육 보정)
3. 부위별 데이터 정규화
4. Stage 3 분석 (상하체 밸런스)
5. 결과 딕셔너리 반환

---

## 🛠️ 개발 작업 내역 (2026-01-20)

### 1. 코드 리팩토링 및 모듈화
**이전 상태**: 
- 단일 파일(`BodyAnalysis_Rule.py`)에 모든 로직이 한 줄로 작성됨
- 함수 기반 구조로 재사용성 낮음
- 예외 처리 부족

**작업 내용**:
- ✅ 전체 코드를 **3개의 모듈로 분리** (`constants.py`, `classifiers.py`, `integration.py`)
- ✅ **모든 로직을 클래스화** (Strategy Pattern 적용)
- ✅ 각 분류 전략을 독립적인 클래스로 구현
- ✅ Facade Pattern으로 복잡한 분석 과정 추상화

### 2. 예외 처리 강화
**문제점**:
- NaN 값 발생 시 프로그램 크래시
- 잘못된 데이터 입력 시 처리 불가
- 디버깅 어려움

**해결 방안**:
- ✅ 모든 분류 메서드에 `try-except` 블록 추가
- ✅ `math.isfinite()` 검사로 NaN/Inf 값 필터링
- ✅ 예외 발생 시 기본값("알 수 없음", 0.0) 반환
- ✅ 디버깅용 에러 로그 출력 추가
- ✅ 안전한 0으로 나누기 방지

### 3. 데이터 타입 유연성 개선
**문제점**:
- 딕셔너리와 객체 형태 데이터 혼용 시 오류
- `BodyCompositionData` 클래스 정의는 있으나 활용 안 됨

**해결 방안**:
- ✅ **`BodyCompositionData.from_dict()` 메서드 구현**
  - 딕셔너리 → 객체 자동 변환
  - 누락된 필드 안전하게 처리
- ✅ `integration.py`에서 입력 데이터 자동 변환
- ✅ `_get_value()` 헬퍼로 딕셔너리/객체 통합 접근
- ✅ 사용자는 원하는 형태로 데이터 입력 가능

### 4. Import 오류 수정
**문제점**:
- 파일명 대소문자 불일치 (`Constants.py` vs `constants.py`)
- 누락된 import 문
- 순환 참조 문제

**해결 방안**:
- ✅ 모든 import 문을 소문자 파일명으로 통일
- ✅ `import constants as Constants` 별칭 사용
- ✅ 필요한 모든 클래스 명시적 import
- ✅ `BodyPartLevel.NORMAL` → `Constants.BodyPartLevel.NORMAL` 수정

### 5. 코드 품질 개선
- ✅ 모든 클래스/메서드에 docstring 추가
- ✅ 타입 힌트 및 주석 보강
- ✅ 매직 넘버 제거 (상수로 정의)
- ✅ 일관된 네이밍 컨벤션 적용
- ✅ 메서드 체이닝 지원 (Builder Pattern)

---

## 🧪 테스트 및 검증

### 테스트 케이스
```python
# main_test.py 실행
analyzer = BodyCompositionAnalyzer(margin=0.10)
result = analyzer.analyze_full_pipeline(user_data)
```

### 검증 항목
- [x] 딕셔너리 입력 정상 작동
- [x] BodyCompositionData 객체 입력 정상 작동
- [x] 자동 변환 기능 동작
- [x] 예외 처리 정상 작동 (NaN, None, 잘못된 값)
- [x] 모든 Stage 분석 결과 출력
- [x] 부위별 분석 정상 작동

---

## 📊 분류 기준 요약

### BMI 분류
| BMI 범위 | 분류 |
|---------|------|
| < 18.5 | 저체중 |
| 18.5 ~ 23.0 | 정상 |
| 23.0 ~ 24.9 | 과체중 |
| 24.9 ~ 29.9 | 비만1단계 |
| 29.9 ~ 34.9 | 비만2단계 |
| ≥ 34.9 | 고도비만 |

### 체지방률 분류
| 체지방률 | 분류 |
|---------|------|
| < 10% | 표준미만 |
| 10% ~ 20% | 표준 |
| 20% ~ 24% | 과체중 |
| ≥ 24% | 비만 |

### 근육량/체중 비율
| 비율 | 근육 레벨 |
|------|----------|
| ≥ 0.55 | 근육 매우 많음 |
| ≥ 0.50 | 근육 많음 |
| ≥ 0.45 | 근육 충분 |
| ≥ 0.40 | 근육 보통 |
| < 0.40 | 근육 적음 |

---

## 🚀 사용 방법

상세한 설치 방법 및 실행 가이드는 실제 코드가 위치한 실험 디렉토리의 README를 참고하세요.

### 👉 [사용 가이드 및 Quick Start 바로가기](../experiments/Rule-based_BodyAnalysis/readme.md)

위 링크를 통해 다음 내용을 확인할 수 있습니다:
1. 테스트 코드 실행 방법 (`main_test.py`)
2. 프로젝트 적용 예시 코드
3. 주요 파일 구조 설명

---

## 📝 참고 사항

### 개발 환경
- Python 3.13
- 외부 라이브러리 의존성 없음 (순수 Python)

### 주의사항
- 모든 수치는 의학적 기준을 참고했으나, **전문적인 의료 진단을 대체할 수 없습니다**
- 임계값은 한국인 기준으로 설정되어 있습니다
- 부위별 분석은 기본 마진 10%를 사용합니다

### 기여자
- 개발자: [Your Name]
- 프로젝트: ExplainMyBody
- 날짜: 2026-01-20

---

## 📚 관련 문서
- [BodyAnalysis_Rule.py](../experiments/Rule-based_BodyAnalysis/BodyAnalysis_Rule.py) - 원본 코드
- [constants.py](../experiments/Rule-based_BodyAnalysis/constants.py) - 상수 정의
- [classifiers.py](../experiments/Rule-based_BodyAnalysis/classifiers.py) - 분류 로직
- [integration.py](../experiments/Rule-based_BodyAnalysis/integration.py) - 통합 파이프라인

---

**Last Updated**: 2026-01-20  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
