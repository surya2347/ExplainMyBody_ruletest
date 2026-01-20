# 결과를 즉시 확인하기 위한 코드
# 임의로 분석한 결과를 출력하는 테스트 코드
# 실제 프로젝트에서는 사용되지 않을 예정



# ============================================================================
# 결과 출력 유틸리티
# ============================================================================

class ResultPrinter:
    """분석 결과 출력"""
    
    @staticmethod
    def print_analysis_result(result):
        """분석 결과를 포맷팅하여 출력"""
        print("\n" + "=" * 60)
        print("체성분 분석 결과")
        print("=" * 60)
        
        # 기본 정보

        print("\n 파일 타입: ", type(result))
        basic = result.get("basic_info", {})
        print(f"\n[기본 정보]")
        print(f"성별: {basic.get('sex', 'N/A')}")
        print(f"나이: {basic.get('age', 'N/A')}세")
        print(f"키: {basic.get('height_cm', 'N/A')}cm")
        print(f"체중: {basic.get('weight_kg', 'N/A')}kg")
        
        # Stage 1+2 결과
        stage12 = result.get("stage1_2", {})
        print(f"\n[Stage 1+2: 체형 분류]")
        print(f"BMI: {stage12.get('bmi', 'N/A')} ({stage12.get('bmi_category', 'N/A')})")
        print(f"체지방 분류: {stage12.get('fat_category', 'N/A')}")
        print(f"근육 비율: {stage12.get('smm_ratio', 'N/A')} ({stage12.get('muscle_level', 'N/A')})")
        print(f"1차 체형: {stage12.get('stage1_type', 'N/A')}")
        print(f"2차 체형 (근육 보정): {stage12.get('stage2_type', 'N/A')}")
        
        # 부위별 분석
        muscle_seg = result.get("muscle_seg")
        fat_seg = result.get("fat_seg")
        
        if muscle_seg:
            print(f"\n[부위별 근육 분포]")
            for part, level in muscle_seg.items():
                print(f"{part}: {level}")
        
        if fat_seg:
            print(f"\n[부위별 체지방 분포]")
            for part, level in fat_seg.items():
                print(f"{part}: {level}")
        
        # Stage 3 결과
        print(f"\n[Stage 3: 상하체 밸런스]")
        print(f"최종 체형: {result.get('stage3', 'N/A')}")
        
        print("\n" + "=" * 60)

        print(result)
