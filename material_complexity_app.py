"""
재질 복잡도 측정기
Material Complexity Analyzer

H (Permutation Entropy) - 무질서도
C (Statistical Complexity) - 구조적 복잡도  
F (Fisher Information) - 경계 선명도

기반: Bariviera et al. (2025) - Hilbert Curve + Information Theory
"""

import streamlit as st
import numpy as np
from PIL import Image
from hilbertcurve.hilbertcurve import HilbertCurve
from math import factorial
import itertools
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="재질 복잡도 측정기",
    page_icon="🎨",
    layout="wide"
)

# 세션 상태 초기화
if 'results_history' not in st.session_state:
    st.session_state.results_history = []

# 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    .metric-card-h {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .metric-card-c {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    .metric-card-f {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    }
    .metric-value {
        font-size: 3rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 1.2rem;
        opacity: 0.9;
    }
    .metric-desc {
        font-size: 0.9rem;
        opacity: 0.8;
        margin-top: 0.5rem;
    }
    .interpretation {
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
        font-weight: 500;
    }
    .interpretation-low {
        background-color: #e8f5e9;
        color: #2e7d32;
    }
    .interpretation-medium {
        background-color: #fff3e0;
        color: #e65100;
    }
    .interpretation-high {
        background-color: #fce4ec;
        color: #c2185b;
    }
    .recommendation-box {
        background-color: #e3f2fd;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1976d2;
        margin: 2rem 0;
    }
    .justification-box {
        background-color: #f3e5f5;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #9c27b0;
        margin: 2rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: 600;
        padding: 0.75rem;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


def hilbert_to_sequence(image_array, size=1024):
    """2D 이미지를 Hilbert Curve로 1D 시퀀스 변환"""
    # Grayscale 변환
    if len(image_array.shape) == 3:
        gray = 0.299 * image_array[:,:,0] + 0.587 * image_array[:,:,1] + 0.114 * image_array[:,:,2]
    else:
        gray = image_array
    
    # 1024×1024 리사이즈
    img_pil = Image.fromarray(gray.astype('uint8'))
    img_pil = img_pil.resize((size, size))
    img_array = np.array(img_pil, dtype=float)
    
    # Hilbert Curve 생성
    n = int(np.log2(size))
    hilbert = HilbertCurve(n, 2)
    
    # 1D sequence 추출
    sequence = []
    for i in range(size * size):
        coords = hilbert.point_from_distance(i)
        pixel_value = img_array[coords[1], coords[0]]
        sequence.append(pixel_value)
    
    return np.array(sequence)


def ordinal_patterns(sequence, D=6, tau=1):
    """Bandt-Pompe ordinal patterns 생성"""
    N = len(sequence)
    patterns = []
    
    for t in range(N - (D-1)*tau):
        sub_seq = [sequence[t + i*tau] for i in range(D)]
        pattern = tuple(np.argsort(sub_seq))
        patterns.append(pattern)
    
    unique_patterns, counts = np.unique(patterns, axis=0, return_counts=True)
    total = len(patterns)
    
    pattern_probs = {}
    for pattern, count in zip(unique_patterns, counts):
        pattern_probs[tuple(pattern)] = count / total
    
    return patterns, pattern_probs


def permutation_entropy(pattern_probs, D=5, normalize=True):
    """H (Permutation Entropy) 계산"""
    S = 0
    for prob in pattern_probs.values():
        if prob > 0:
            S -= prob * np.log(prob)
    
    if normalize:
        max_entropy = np.log(factorial(D))
        H = S / max_entropy
    else:
        H = S
    
    return H


def statistical_complexity(pattern_probs, D=5):
    """C_JS (Statistical Complexity) 계산"""
    num_patterns = int(factorial(D))
    p_e = 1.0 / num_patterns
    
    P = np.zeros(num_patterns)
    for i, pattern in enumerate(itertools.permutations(range(D))):
        if pattern in pattern_probs:
            P[i] = pattern_probs[pattern]
        else:
            P[i] = 0
    
    P_e = np.ones(num_patterns) * p_e
    
    def shannon_entropy(probs):
        S = 0
        for p in probs:
            if p > 0:
                S -= p * np.log(p)
        return S
    
    S_P = shannon_entropy(P)
    S_Pe = shannon_entropy(P_e)
    S_avg = shannon_entropy((P + P_e) / 2)
    
    J = S_avg - 0.5*S_P - 0.5*S_Pe
    
    Q_0 = -2 * ((num_patterns+1)/num_patterns * np.log(num_patterns+1) 
                - 2*np.log(2*num_patterns) + np.log(num_patterns))**(-1)
    
    Q_J = J / Q_0 if Q_0 != 0 else 0
    
    H = permutation_entropy(pattern_probs, D, normalize=True)
    
    C_JS = Q_J * H
    
    return C_JS


def fisher_information(pattern_probs, D=5):
    """F (Fisher Information) 계산"""
    all_patterns = list(itertools.permutations(range(D)))
    all_patterns_sorted = sorted(all_patterns)
    
    probs = []
    for pattern in all_patterns_sorted:
        if pattern in pattern_probs:
            probs.append(pattern_probs[pattern])
        else:
            probs.append(0)
    
    probs = np.array(probs)
    
    F_sum = 0
    for j in range(len(probs) - 1):
        diff = np.sqrt(probs[j+1]) - np.sqrt(probs[j])
        F_sum += diff**2
    
    if np.max(probs) == 1 and np.sum(probs > 0) == 1:
        if np.argmax(probs) in [0, len(probs)-1]:
            F_0 = 1
        else:
            F_0 = 0.5
    else:
        F_0 = 0.5
    
    F = F_0 * F_sum
    
    return F


def measure_complexity(image_array):
    """재질 이미지의 H, C, F 측정"""
    sequence = hilbert_to_sequence(image_array, size=1024)
    patterns, pattern_probs = ordinal_patterns(sequence, D=6, tau=1)
    
    H = permutation_entropy(pattern_probs, D=6, normalize=True)
    C = statistical_complexity(pattern_probs, D=6)
    F = fisher_information(pattern_probs, D=6)
    
    return H, C, F


def interpret_value(value, metric_type):
    """값에 대한 해석 생성"""
    if metric_type == 'H':
        if value < 0.3:
            level = "낮음"
            meaning = "규칙적인 패턴"
            color = "low"
        elif value < 0.7:
            level = "중간"
            meaning = "부분적 패턴"
            color = "medium"
        else:
            level = "높음"
            meaning = "불규칙한 패턴"
            color = "high"
    
    elif metric_type == 'C':
        if value < 0.3:
            level = "낮음"
            meaning = "단순한 구조"
            color = "low"
        elif value < 0.7:
            level = "중간"
            meaning = "정교한 구조"
            color = "medium"
        else:
            level = "높음"
            meaning = "복잡한 구조"
            color = "high"
    
    else:  # F
        if value < 0.3:
            level = "낮음"
            meaning = "부드러운 경계"
            color = "low"
        elif value < 0.7:
            level = "중간"
            meaning = "중간 선명도"
            color = "medium"
        else:
            level = "높음"
            meaning = "날카로운 경계"
            color = "high"
    
    return level, meaning, color


# 메인 앱
st.markdown('<div class="main-header">🎨 재질 복잡도 측정기</div>', unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center; color: #666; margin-bottom: 2rem;'>
재질 이미지를 업로드하면 <strong>H, C, F</strong> 세 가지 복잡도 지표를 자동으로 측정합니다
</div>
""", unsafe_allow_html=True)

# 사이드바 - 측정 기록
with st.sidebar:
    st.markdown("### 📊 측정 기록")
    
    if st.session_state.results_history:
        st.caption(f"총 {len(st.session_state.results_history)}개 측정됨")
        
        if st.button("🗑️ 기록 전체 삭제"):
            st.session_state.results_history = []
            st.rerun()
        
        st.markdown("---")
        
        # 간단한 요약
        for idx, result in enumerate(reversed(st.session_state.results_history)):
            with st.expander(f"{idx+1}. {result['filename'][:20]}..."):
                st.write(f"H: {result['H']:.3f}")
                st.write(f"C: {result['C']:.3f}")
                st.write(f"F: {result['F']:.3f}")
                st.caption(result['timestamp'])
    else:
        st.info("아직 측정 기록이 없습니다")
    
    st.markdown("---")
    st.markdown("### ℹ️ 정보")
    st.caption("이미지 크기: 1024×1024")
    st.caption("Embedding: D=5, τ=1")
    st.caption("계산 시간: ~1-2분")

# 파일 업로드
uploaded_file = st.file_uploader(
    "재질 이미지 업로드 (JPG, PNG)",
    type=['jpg', 'jpeg', 'png'],
    help="Albedo 또는 Normal map 이미지를 업로드하세요"
)

if uploaded_file is not None:
    # 이미지 로드
    image = Image.open(uploaded_file)
    image_array = np.array(image)
    
    # 이미지 표시
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(image, caption='업로드된 이미지', use_container_width=True)
    
    # 측정 버튼
    if st.button("🔍 복잡도 측정하기", use_container_width=True):
        with st.spinner('측정 중... (약 1-2분 소요)'):
            # 측정
            H, C, F = measure_complexity(image_array)
            
            # 기록 저장
            result_data = {
                'filename': uploaded_file.name,
                'H': H,
                'C': C,
                'F': F,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.results_history.append(result_data)
            
            # 해석
            h_level, h_meaning, h_color = interpret_value(H, 'H')
            c_level, c_meaning, c_color = interpret_value(C, 'C')
            f_level, f_meaning, f_color = interpret_value(F, 'F')
            
            st.success('✅ 측정 완료!')
            
            # 결과 표시
            st.markdown("---")
            st.markdown("## 📊 측정 결과")
            
            # 3개 컬럼
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card metric-card-h">
                    <div class="metric-label">H (무질서도)</div>
                    <div class="metric-value">{H:.3f}</div>
                    <div class="metric-desc">패턴의 예측 불가능성</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="interpretation interpretation-{h_color}">
                    <strong>{h_level}:</strong> {h_meaning}
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("자세히 보기"):
                    st.markdown("""
                    **H (Permutation Entropy) - 무질서도**
                    
                    패턴의 다양성과 예측 불가능성을 측정합니다.
                    
                    - **0.0~0.2:** 규칙적, 반복적 (단색, 줄무늬)
                    - **0.3~0.7:** 중간 (부분적 패턴)
                    - **0.8~1.0:** 불규칙, 무작위 (노이즈, 거친 표면)
                    
                    💡 픽셀 값(0-255)의 순서 패턴이 얼마나 다양한가를 측정
                    """)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card metric-card-c">
                    <div class="metric-label">C (구조 복잡도)</div>
                    <div class="metric-value">{C:.3f}</div>
                    <div class="metric-desc">조직화된 구조의 정도</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="interpretation interpretation-{c_color}">
                    <strong>{c_level}:</strong> {c_meaning}
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("자세히 보기"):
                    st.markdown("""
                    **C (Statistical Complexity) - 구조적 조직**
                    
                    복잡한 조직과 구조의 정도를 측정합니다.
                    
                    - **0.0~0.2:** 단순 또는 완전 무작위 (단색 OR 노이즈)
                    - **0.4~0.8:** 복잡하면서 조직적 (나뭇결, 대리석, 직물)
                    - **기타:** 중간
                    
                    💡 단순히 복잡하기만 한 것이 아닌, 구조적 깊이를 측정
                    """)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card metric-card-f">
                    <div class="metric-label">F (경계 선명도)</div>
                    <div class="metric-value">{F:.3f}</div>
                    <div class="metric-desc">국소적 변화의 급격함</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="interpretation interpretation-{f_color}">
                    <strong>{f_level}:</strong> {f_meaning}
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("자세히 보기"):
                    st.markdown("""
                    **F (Fisher Information) - 지역적 변화**
                    
                    국소적 변화의 급격함을 측정합니다.
                    
                    - **0.0~0.2:** 완만, 부드러움 (그라데이션, 광택 표면)
                    - **0.3~0.7:** 중간
                    - **0.7~1.0:** 급격, 날카로움 (강한 대비, 거친 암석)
                    
                    💡 픽셀 간 밝기 차이가 얼마나 급격한가를 측정
                    """)
            
            # 방법론 정당성
            st.markdown("---")
            st.markdown("""
            <div class="justification-box">
                <h3>🔬 왜 이 방법을 사용하나요?</h3>
                <p style='margin-top: 1rem;'>
                본 측정 방법은 Bariviera et al. (2025)의 검증된 방법론을 기반으로 합니다:
                </p>
                <ul style='margin-top: 1rem;'>
                    <li><strong>다차원적 분석:</strong> H, C, F 세 지표가 재질의 무질서도, 구조, 변화를 동시에 포착</li>
                    <li><strong>회전 불변성:</strong> 이미지 회전에도 일관된 결과 (Hilbert Curve 사용)</li>
                    <li><strong>방향 편향 제거:</strong> 행/열 스캔 방식의 편향 없음</li>
                    <li><strong>객관적 정량화:</strong> 주관적 판단이 아닌 정보이론 기반 측정</li>
                </ul>
                <p style='color: #666; margin-top: 1rem; font-size: 0.9rem;'>
                    논문: "Rotation invariant patterns based on Hilbert curve" <br>
                    Pattern Analysis and Applications (2025)
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # 권장사항
            st.markdown("""
            <div class="recommendation-box">
                <h3>💡 어떤 지표를 사용해야 하나요?</h3>
                <p style='font-size: 1.1rem; margin-top: 1rem;'>
                    <strong>목적에 따라 선택하세요:</strong>
                </p>
                <ul style='margin-top: 1rem;'>
                    <li><strong>H:</strong> 전반적인 불규칙성/다양성 측정</li>
                    <li><strong>C:</strong> 구조적 복잡도와 조직화 정도</li>
                    <li><strong>F:</strong> 경계 선명도와 국소적 거칠기</li>
                </ul>
                <p style='color: #666; margin-top: 1rem;'>
                    세 지표를 함께 사용하면 재질의 특성을 종합적으로 이해할 수 있습니다.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # CSV 다운로드
            st.markdown("---")
            st.markdown("### 📥 결과 다운로드")
            
            csv_data = f"filename,H,C,F\n{uploaded_file.name},{H:.4f},{C:.4f},{F:.4f}"
            st.download_button(
                label="📄 이 결과만 CSV로 다운로드",
                data=csv_data,
                file_name=f"complexity_{uploaded_file.name.split('.')[0]}.csv",
                mime="text/csv"
            )

# 비교 테이블
if st.session_state.results_history:
    st.markdown("---")
    st.markdown("## 📈 측정 결과 비교")
    
    # DataFrame 생성
    df = pd.DataFrame(st.session_state.results_history)
    df = df[['filename', 'H', 'C', 'F', 'timestamp']]
    
    # 소수점 정리
    df['H'] = df['H'].apply(lambda x: f"{x:.3f}")
    df['C'] = df['C'].apply(lambda x: f"{x:.3f}")
    df['F'] = df['F'].apply(lambda x: f"{x:.3f}")
    
    st.dataframe(df, use_container_width=True)
    
    # 전체 다운로드
    csv_all = df.to_csv(index=False)
    st.download_button(
        label="📊 전체 결과 CSV로 다운로드",
        data=csv_all,
        file_name=f"all_complexity_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

else:
    # 사용 안내
    st.info("👆 위에서 재질 이미지를 업로드하세요")
    
    # 예시 설명
    st.markdown("---")
    st.markdown("## 📖 사용 가이드")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 지원 이미지
        - **Albedo/Base Color:** 재질의 색상, 패턴
        - **Normal Map:** 재질의 표면 구조
        - **형식:** JPG, PNG
        - **권장 크기:** 512×512 이상
        """)
    
    with col2:
        st.markdown("""
        ### 측정 지표
        - **H:** 무질서도 (패턴의 다양성)
        - **C:** 구조 복잡도 (조직화 정도)
        - **F:** 지역적 변화 (경계 선명도)
        """)
    
    st.markdown("---")
    st.markdown("""
    ### ❓ 자주 묻는 질문
    
    **Q: 어떤 지표를 써야 하나요?**  
    A: 목적에 따라 다릅니다. H는 전반적 복잡도, C는 구조적 특성, F는 표면 거칠기를 나타냅니다.
    
    **Q: 측정이 오래 걸려요**  
    A: 1024×1024 크기로 계산하므로 1-2분 정도 소요됩니다. 정확도를 위한 것입니다.
    
    **Q: 여러 재질을 비교하고 싶어요**  
    A: 하나씩 측정하면 자동으로 기록됩니다. 왼쪽 사이드바와 하단 비교표를 확인하세요.
    """)

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; padding: 2rem;'>
    <p>Material Complexity Analyzer v2.0</p>
    <p style='font-size: 0.9rem;'>
        Based on: Hilbert Curve + Information Theory<br>
        Bariviera et al. (2025) - Pattern Analysis and Applications
    </p>
    <p style='font-size: 0.8rem; margin-top: 1rem;'>
        측정 방식: 1024×1024 리샘플링 | D=5, τ=1 | Grayscale 변환
    </p>
</div>
""", unsafe_allow_html=True)
