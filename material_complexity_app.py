"""
재질 복잡도 측정기 (프랙탈 차원 버전)
Material Complexity Analyzer - Fractal Dimension

FD (Fractal Dimension) - 기하학적 복잡도
L (Lacunarity) - 패턴 불균일성
C (Combined) - 종합 복잡도
"""

import streamlit as st
import numpy as np
from PIL import Image
import cv2
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

# 스타일 (동일)
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
    .metric-card-fd {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .metric-card-l {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    .metric-card-c {
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
        color: #1a1a1a;
    }
    .recommendation-box h3 {
        color: #1565c0;
    }
    .recommendation-box strong {
        color: #0d47a1;
    }
    .justification-box {
        background-color: #f3e5f5;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #9c27b0;
        margin: 2rem 0;
        color: #1a1a1a;
    }
    .justification-box h3 {
        color: #7b1fa2;
    }
    .justification-box strong {
        color: #6a1b9a;
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


def box_count(image, box_size):
    """박스 카운팅"""
    h, w = image.shape
    n_boxes_h = h // box_size
    n_boxes_w = w // box_size
    
    count = 0
    for i in range(n_boxes_h):
        for j in range(n_boxes_w):
            box = image[i*box_size:(i+1)*box_size, 
                       j*box_size:(j+1)*box_size]
            if box.max() - box.min() > 0:
                count += 1
    
    return count


def fractal_dimension(image_array):
    """프랙탈 차원 계산"""
    if len(image_array.shape) == 3:
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_array
    
    edges = cv2.Canny(gray, 50, 150)
    
    box_sizes = [2, 4, 8, 16, 32, 64]
    counts = []
    
    for size in box_sizes:
        count = box_count(edges, size)
        counts.append(count)
    
    box_sizes = np.array(box_sizes, dtype=float)
    counts = np.array(counts, dtype=float)
    
    valid = counts > 0
    box_sizes = box_sizes[valid]
    counts = counts[valid]
    
    if len(counts) < 2:
        return 1.0
    
    coeffs = np.polyfit(np.log(box_sizes), np.log(counts), 1)
    FD = -coeffs[0]
    
    FD = np.clip(FD, 1.0, 2.0)
    
    return FD


def lacunarity(image_array):
    """Lacunarity 계산"""
    if len(image_array.shape) == 3:
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_array
    
    box_size = 32
    h, w = gray.shape
    
    masses = []
    for i in range(0, h-box_size, 8):
        for j in range(0, w-box_size, 8):
            box = gray[i:i+box_size, j:j+box_size]
            mass = np.sum(box > 128)
            masses.append(mass)
    
    masses = np.array(masses)
    
    if len(masses) == 0 or np.mean(masses) == 0:
        return 0.0
    
    L = (np.std(masses) / np.mean(masses)) ** 2
    L = min(L / 2.0, 1.0)
    
    return L


def measure_complexity(image_array):
    """재질 복잡도 측정"""
    FD = fractal_dimension(image_array)
    L = lacunarity(image_array)
    
    FD_norm = (FD - 1.0) / 1.0
    C = 0.7 * FD_norm + 0.3 * L
    
    return FD, L, C


def interpret_value(value, metric_type):
    """값 해석"""
    if metric_type == 'FD':
        if value < 1.2:
            return "낮음", "단순한 패턴", "low"
        elif value < 1.6:
            return "중간", "중간 복잡도", "medium"
        else:
            return "높음", "복잡한 패턴", "high"
    
    elif metric_type == 'L':
        if value < 0.3:
            return "낮음", "균일한 분포", "low"
        elif value < 0.6:
            return "중간", "중간 불균일", "medium"
        else:
            return "높음", "불균일 분포", "high"
    
    else:  # C
        if value < 0.3:
            return "낮음", "단순함", "low"
        elif value < 0.6:
            return "중간", "중간 복잡도", "medium"
        else:
            return "높음", "복잡함", "high"


# 메인 앱
st.markdown('<div class="main-header">🎨 재질 복잡도 측정기</div>', unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center; color: #666; margin-bottom: 2rem;'>
재질 이미지를 업로드하면 <strong>FD, L, C</strong> 세 가지 복잡도 지표를 자동으로 측정합니다
</div>
""", unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.markdown("### 📊 측정 기록")
    
    if st.session_state.results_history:
        st.caption(f"총 {len(st.session_state.results_history)}개 측정됨")
        
        if st.button("🗑️ 기록 전체 삭제"):
            st.session_state.results_history = []
            st.rerun()
        
        st.markdown("---")
        
        for idx, result in enumerate(reversed(st.session_state.results_history)):
            with st.expander(f"{idx+1}. {result['filename'][:20]}..."):
                st.write(f"FD: {result['FD']:.3f}")
                st.write(f"L: {result['L']:.3f}")
                st.write(f"C: {result['C']:.3f}")
                st.caption(result['timestamp'])
    else:
        st.info("아직 측정 기록이 없습니다")
    
    st.markdown("---")
    st.markdown("### ℹ️ 정보")
    st.caption("방법: Box-Counting")
    st.caption("측정: 엣지 기반")
    st.caption("계산 시간: ~1-2초")

# 파일 업로드
uploaded_file = st.file_uploader(
    "재질 이미지 업로드 (JPG, PNG)",
    type=['jpg', 'jpeg', 'png'],
    help="호텔 바닥 재질 이미지를 업로드하세요"
)

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    image_array = np.array(image)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(image, caption='업로드된 이미지', use_container_width=True)
    
    if st.button("🔍 복잡도 측정하기", use_container_width=True):
        with st.spinner('측정 중... (약 1-2초)'):
            FD, L, C = measure_complexity(image_array)
            
            result_data = {
                'filename': uploaded_file.name,
                'FD': FD,
                'L': L,
                'C': C,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.results_history.append(result_data)
            
            fd_level, fd_meaning, fd_color = interpret_value(FD, 'FD')
            l_level, l_meaning, l_color = interpret_value(L, 'L')
            c_level, c_meaning, c_color = interpret_value(C, 'C')
            
            st.success('✅ 측정 완료!')
            
            st.markdown("---")
            st.markdown("## 📊 측정 결과")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card metric-card-fd">
                    <div class="metric-label">FD (프랙탈 차원)</div>
                    <div class="metric-value">{FD:.3f}</div>
                    <div class="metric-desc">기하학적 복잡도</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="interpretation interpretation-{fd_color}">
                    <strong>{fd_level}:</strong> {fd_meaning}
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("자세히 보기"):
                    st.markdown("""
                    **FD (Fractal Dimension)**
                    
                    엣지 패턴의 기하학적 복잡도를 측정합니다.
                    
                    - **1.0~1.2:** 단순 (단색, 격자)
                    - **1.2~1.6:** 중간 (타일, 나뭇결)
                    - **1.6~2.0:** 복잡 (프랙탈, 자연재)
                    
                    💡 1차원(선) ~ 2차원(면)의 복잡도
                    """)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card metric-card-l">
                    <div class="metric-label">L (틈새도)</div>
                    <div class="metric-value">{L:.3f}</div>
                    <div class="metric-desc">패턴 불균일성</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="interpretation interpretation-{l_color}">
                    <strong>{l_level}:</strong> {l_meaning}
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("자세히 보기"):
                    st.markdown("""
                    **L (Lacunarity)**
                    
                    패턴의 균일성 vs 불균일성을 측정합니다.
                    
                    - **0.0~0.3:** 균일 (반복 패턴)
                    - **0.3~0.6:** 중간
                    - **0.6~1.0:** 불균일 (불규칙 배치)
                    
                    💡 패턴의 "틈새" 정도
                    """)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card metric-card-c">
                    <div class="metric-label">C (종합 복잡도)</div>
                    <div class="metric-value">{C:.3f}</div>
                    <div class="metric-desc">FD + L 결합</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="interpretation interpretation-{c_color}">
                    <strong>{c_level}:</strong> {c_meaning}
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("자세히 보기"):
                    st.markdown("""
                    **C (Combined Complexity)**
                    
                    FD와 L를 결합한 종합 복잡도입니다.
                    
                    - **0.0~0.3:** 단순
                    - **0.3~0.6:** 중간
                    - **0.6~1.0:** 복잡
                    
                    💡 C = 0.7×FD + 0.3×L
                    """)
            
            st.markdown("---")
            st.markdown("""
            <div class="justification-box">
                <h3>🔬 왜 프랙탈 차원을 사용하나요?</h3>
                <p style='margin-top: 1rem;'>
                프랙탈 차원은 기하학적 패턴 분석에 최적화된 방법입니다:
                </p>
                <ul style='margin-top: 1rem;'>
                    <li><strong>직관적:</strong> 시각적 복잡도와 일치</li>
                    <li><strong>빠름:</strong> 엣지 기반 계산 (1-2초)</li>
                    <li><strong>효율적:</strong> 메모리 사용 최소</li>
                    <li><strong>변별력:</strong> 패턴 유형 잘 구분</li>
                </ul>
                <p style='color: #666; margin-top: 1rem; font-size: 0.9rem;'>
                    Box-Counting Method + Lacunarity Analysis
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="recommendation-box">
                <h3>💡 어떤 지표를 사용해야 하나요?</h3>
                <p style='font-size: 1.1rem; margin-top: 1rem;'>
                    <strong>목적에 따라 선택하세요:</strong>
                </p>
                <ul style='margin-top: 1rem;'>
                    <li><strong>FD:</strong> 패턴의 기하학적 복잡도</li>
                    <li><strong>L:</strong> 패턴의 균일성/불균일성</li>
                    <li><strong>C:</strong> 종합적인 복잡도 (추천)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 📥 결과 다운로드")
            
            csv_data = f"filename,FD,L,C\n{uploaded_file.name},{FD:.4f},{L:.4f},{C:.4f}"
            st.download_button(
                label="📄 이 결과만 CSV로 다운로드",
                data=csv_data,
                file_name=f"complexity_{uploaded_file.name.split('.')[0]}.csv",
                mime="text/csv"
            )

if st.session_state.results_history:
    st.markdown("---")
    st.markdown("## 📈 측정 결과 비교")
    
    df = pd.DataFrame(st.session_state.results_history)
    df = df[['filename', 'FD', 'L', 'C', 'timestamp']]
    
    df['FD'] = df['FD'].apply(lambda x: f"{x:.3f}")
    df['L'] = df['L'].apply(lambda x: f"{x:.3f}")
    df['C'] = df['C'].apply(lambda x: f"{x:.3f}")
    
    st.dataframe(df, use_container_width=True)
    
    csv_all = df.to_csv(index=False)
    st.download_button(
        label="📊 전체 결과 CSV로 다운로드",
        data=csv_all,
        file_name=f"all_complexity_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

else:
    st.info("👆 위에서 재질 이미지를 업로드하세요")
    
    st.markdown("---")
    st.markdown("## 📖 사용 가이드")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 지원 이미지
        - **호텔 바닥 재질**
        - **타일, 대리석, 카펫 등**
        - **형식:** JPG, PNG
        - **권장 크기:** 512×512 이상
        """)
    
    with col2:
        st.markdown("""
        ### 측정 지표
        - **FD:** 기하학적 복잡도 (1.0~2.0)
        - **L:** 패턴 불균일성 (0~1)
        - **C:** 종합 복잡도 (0~1)
        """)

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; padding: 2rem;'>
    <p>Material Complexity Analyzer v3.0 (Fractal)</p>
    <p style='font-size: 0.9rem;'>
        Box-Counting Fractal Dimension + Lacunarity Analysis
    </p>
    <p style='font-size: 0.8rem; margin-top: 1rem;'>
        측정 방식: Canny Edge Detection + Box-Counting
    </p>
</div>
""", unsafe_allow_html=True)
