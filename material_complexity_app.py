"""
재질 복잡도 측정기
Material Complexity Analyzer

H (Permutation Entropy) - 무질서도
C (Statistical Complexity) - 구조적 복잡도  
F (Fisher Information) - 경계 선명도
"""

import streamlit as st
import numpy as np
from PIL import Image
from hilbertcurve.hilbertcurve import HilbertCurve
from math import factorial  # ← 여기 수정!
import itertools
import io

# 페이지 설정
st.set_page_config(
    page_title="재질 복잡도 측정기",
    page_icon="🎨",
    layout="wide"
)

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


def hilbert_to_sequence(image_array, size=512):
    """2D 이미지를 Hilbert Curve로 1D 시퀀스 변환"""
    # Grayscale 변환
    if len(image_array.shape) == 3:
        gray = 0.299 * image_array[:,:,0] + 0.587 * image_array[:,:,1] + 0.114 * image_array[:,:,2]
    else:
        gray = image_array
    
    # 512x512 리사이즈
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


def ordinal_patterns(sequence, D=5, tau=1):
    """Bandt-Pompe ordinal patterns 생성"""
    N = len(sequence)
    patterns = []
    
    # 부분 시퀀스 추출 및 패턴 변환
    for t in range(N - (D-1)*tau):
        sub_seq = [sequence[t + i*tau] for i in range(D)]
        pattern = tuple(np.argsort(sub_seq))
        patterns.append(pattern)
    
    # 확률 분포 계산
    unique_patterns, counts = np.unique(patterns, axis=0, return_counts=True)
    total = len(patterns)
    
    pattern_probs = {}
    for pattern, count in zip(unique_patterns, counts):
        pattern_probs[tuple(pattern)] = count / total
    
    return patterns, pattern_probs


def permutation_entropy(pattern_probs, D=5, normalize=True):
    """H (Permutation Entropy) 계산"""
    # Shannon Entropy
    S = 0
    for prob in pattern_probs.values():
        if prob > 0:
            S -= prob * np.log(prob)
    
    # 정규화
    if normalize:
        max_entropy = np.log(factorial(D))
        H = S / max_entropy
    else:
        H = S
    
    return H


def statistical_complexity(pattern_probs, D=5):
    """C_JS (Statistical Complexity) 계산"""
    # P_e: 균등 분포
    num_patterns = int(factorial(D))  # ← int() 추가!
    p_e = 1.0 / num_patterns
    
    # P 분포 (실제)
    P = np.zeros(num_patterns)
    for i, pattern in enumerate(itertools.permutations(range(D))):
        if pattern in pattern_probs:
            P[i] = pattern_probs[pattern]
        else:
            P[i] = 0
    
    # P_e 분포
    P_e = np.ones(num_patterns) * p_e
    
    # Jensen-Shannon Divergence
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
    
    # Q_0 정규화 상수
    Q_0 = -2 * ((num_patterns+1)/num_patterns * np.log(num_patterns+1) 
                - 2*np.log(2*num_patterns) + np.log(num_patterns))**(-1)
    
    # Q_J
    Q_J = J / Q_0 if Q_0 != 0 else 0
    
    # H 계산
    H = permutation_entropy(pattern_probs, D, normalize=True)
    
    # C_JS
    C_JS = Q_J * H
    
    return C_JS


def fisher_information(pattern_probs, D=5):
    """F (Fisher Information) 계산"""
    # 모든 가능한 패턴을 Lehmer code 순서로 정렬
    all_patterns = list(itertools.permutations(range(D)))
    all_patterns_sorted = sorted(all_patterns)
    
    # 확률 배열 생성
    probs = []
    for pattern in all_patterns_sorted:
        if pattern in pattern_probs:
            probs.append(pattern_probs[pattern])
        else:
            probs.append(0)
    
    probs = np.array(probs)
    
    # Fisher Information 계산
    F_sum = 0
    for j in range(len(probs) - 1):
        diff = np.sqrt(probs[j+1]) - np.sqrt(probs[j])
        F_sum += diff**2
    
    # F_0 정규화 상수
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
    """
    재질 이미지의 H, C, F 측정
    """
    # Step 1: Hilbert Curve → 1D sequence
    sequence = hilbert_to_sequence(image_array, size=512)
    
    # Step 2: Ordinal patterns → Probability distribution
    patterns, pattern_probs = ordinal_patterns(sequence, D=5, tau=1)
    
    # Step 3: Calculate H, C_JS, F
    H = permutation_entropy(pattern_probs, D=5, normalize=True)
    C = statistical_complexity(pattern_probs, D=5)
    F = fisher_information(pattern_probs, D=5)
    
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
        with st.spinner('측정 중... (약 30초-1분 소요)'):
            # 측정
            H, C, F = measure_complexity(image_array)
            
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
                    <div class="metric-desc">얼마나 예측 불가능한가?</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="interpretation interpretation-{h_color}">
                    <strong>{h_level}:</strong> {h_meaning}
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("자세히 보기"):
                    st.markdown("""
                    **H (Permutation Entropy)**
                    
                    - **0.0~0.3:** 규칙적 (줄무늬, 타일)
                    - **0.3~0.7:** 중간 (부분적 패턴)
                    - **0.7~1.0:** 불규칙 (자연재, 노이즈)
                    
                    💡 **시각적 복잡도**와 가장 일치 (r=0.685)
                    
                    **추천:** "복잡해 보이는 정도" 연구에 사용
                    """)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card metric-card-c">
                    <div class="metric-label">C (구조 복잡도)</div>
                    <div class="metric-value">{C:.3f}</div>
                    <div class="metric-desc">얼마나 정교한 패턴인가?</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="interpretation interpretation-{c_color}">
                    <strong>{c_level}:</strong> {c_meaning}
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("자세히 보기"):
                    st.markdown("""
                    **C (Statistical Complexity)**
                    
                    - **0.0~0.3:** 단순 (극단적)
                    - **0.3~0.7:** 정교한 구조
                    - **0.7~1.0:** 복잡한 패턴
                    
                    ⚠️ **H와 반대 경향** (r=-0.94)
                    
                    **사용:** 패턴 구조 분석
                    """)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card metric-card-f">
                    <div class="metric-label">F (경계 선명도)</div>
                    <div class="metric-value">{F:.3f}</div>
                    <div class="metric-desc">경계가 얼마나 선명한가?</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="interpretation interpretation-{f_color}">
                    <strong>{f_level}:</strong> {f_meaning}
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("자세히 보기"):
                    st.markdown("""
                    **F (Fisher Information)**
                    
                    - **0.0~0.3:** 부드러움 (그라데이션)
                    - **0.3~0.7:** 중간
                    - **0.7~1.0:** 날카로움 (선명)
                    
                    ℹ️ **C와 유사** (r=0.72)
                    
                    **사용:** 경계/질감 연구 (선택)
                    """)
            
            # 권장사항
            st.markdown("---")
            st.markdown("""
            <div class="recommendation-box">
                <h3>💡 어떤 지표를 사용해야 하나요?</h3>
                <p style='font-size: 1.1rem; margin-top: 1rem;'>
                    <strong>"복잡해 보이는 정도"</strong>를 연구하신다면 
                    <span style='background: #ffeb3b; padding: 0.2rem 0.5rem; border-radius: 4px; color: #000;'>
                    <strong>H (무질서도)</strong></span>를 사용하세요.
                </p>
                <p style='color: #666; margin-top: 1rem;'>
                    검증 연구 결과, H가 주관적 복잡도 평가와 가장 일치했습니다 (r=0.685, p<0.001).
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # CSV 다운로드
            st.markdown("---")
            st.markdown("### 📥 결과 다운로드")
            
            csv_data = f"filename,H,C,F\n{uploaded_file.name},{H:.4f},{C:.4f},{F:.4f}"
            st.download_button(
                label="📄 CSV로 다운로드",
                data=csv_data,
                file_name=f"complexity_{uploaded_file.name.split('.')[0]}.csv",
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
        - **H:** 시각적 복잡도 (주관 평가 일치)
        - **C:** 구조적 복잡도 (패턴 분석)
        - **F:** 경계 선명도 (질감 분석)
        """)
    
    st.markdown("---")
    st.markdown("""
    ### ❓ 자주 묻는 질문
    
    **Q: 어떤 지표를 써야 하나요?**  
    A: 대부분의 경우 **H (무질서도)**를 사용하세요. "복잡해 보이는 정도"와 가장 일치합니다.
    
    **Q: 측정이 오래 걸려요**  
    A: 512×512 크기로 자동 변환하므로 30초-1분 정도 소요됩니다.
    
    **Q: Albedo와 Normal 중 뭘 측정하나요?**  
    A: 둘 다 측정 가능합니다. 각각 다른 복잡도 정보를 제공합니다.
    """)

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; padding: 2rem;'>
    <p>Material Complexity Analyzer v2.0</p>
    <p style='font-size: 0.9rem;'>
        Based on: Hilbert Curve + Permutation Entropy (Bariviera et al., 2025)
    </p>
</div>
""", unsafe_allow_html=True)
