"""
재질 복잡도 측정기
Material Complexity Analyzer

FD (Fractal Dimension) - 기하학적 복잡도
L (Lacunarity) - 패턴 불균일성

Box-Counting Method
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
    .metric-card-fd {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .metric-card-l {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
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
    .interpretation-preferred {
        background-color: #e1f5fe;
        color: #01579b;
        border-left: 4px solid #0288d1;
    }
    .info-box {
        background-color: #f3e5f5;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #9c27b0;
        margin: 2rem 0;
        color: #1a1a1a;
    }
    .info-box h3 {
        color: #7b1fa2;
    }
    .info-box strong {
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
    """프랙탈 차원 계산 (Box-Counting Method)"""
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
    
    return FD, L


def interpret_fd(value):
    """FD 값 해석"""
    if value < 1.2:
        return "매우 단순", "단순한 패턴", "low"
    elif value < 1.4:
        return "선호 범위 (하)", "편안한 복잡도", "preferred"
    elif value < 1.7:
        return "선호 범위 (상)", "흥미로운 복잡도", "preferred"
    elif value < 1.8:
        return "복잡", "높은 복잡도", "high"
    else:
        return "매우 복잡", "매우 높은 복잡도", "high"


def interpret_l(value):
    """L 값 해석"""
    if value < 0.3:
        return "균일함", "규칙적 배치", "low"
    elif value < 0.6:
        return "중간", "중간 불균일", "medium"
    else:
        return "불균일함", "불규칙 배치", "high"


# 메인 앱
st.markdown('<div class="main-header">🎨 재질 복잡도 측정기</div>', unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center; color: #666; margin-bottom: 2rem;'>
재질 이미지의 <strong>프랙탈 차원(FD)</strong>과 <strong>불균일성(L)</strong>을 측정합니다
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
            FD, L = measure_complexity(image_array)
            
            result_data = {
                'filename': uploaded_file.name,
                'FD': FD,
                'L': L,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.results_history.append(result_data)
            
            fd_level, fd_meaning, fd_color = interpret_fd(FD)
            l_level, l_meaning, l_color = interpret_l(L)
            
            st.success('✅ 측정 완료!')
            
            st.markdown("---")
            st.markdown("## 📊 측정 결과")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card metric-card-fd">
                    <div class="metric-label">FD (Fractal Dimension)</div>
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
                    
                    - **1.0~1.2:** 매우 단순 (단색, 격자)
                    - **1.2~1.4:** 선호 범위 (하) - 편안함
                    - **1.4~1.7:** 선호 범위 (상) - 흥미로움
                    - **1.7~2.0:** 복잡함
                    
                    💡 **선호 범위 (1.2~1.7)**는 연구에서 입증된 
                    인지적 회복을 촉진하는 범위입니다.
                    
                    📚 [Fractal Dimension이란?](https://en.wikipedia.org/wiki/Fractal_dimension)
                    """)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card metric-card-l">
                    <div class="metric-label">L (Lacunarity)</div>
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
                    
                    패턴의 공간적 분포 특성을 측정합니다.
                    
                    - **0.0~0.3:** 균일한 반복 패턴
                    - **0.3~0.6:** 중간 불균일
                    - **0.6~1.0:** 불규칙 배치
                    
                    💡 같은 FD를 가져도 L이 다르면 
                    다른 시각적 특성을 나타냅니다.
                    
                    📚 [Lacunarity란?](https://en.wikipedia.org/wiki/Lacunarity)
                    """)
            
            # 방법론 설명
            st.markdown("---")
            st.markdown("""
            <div class="info-box">
                <h3>🔬 측정 방법</h3>
                <p style='margin-top: 1rem;'>
                본 애플리케이션은 <strong>Box-Counting Method</strong>를 사용하여 
                프랙탈 차원을 계산합니다.
                </p>
                <ul style='margin-top: 1rem;'>
                    <li><strong>FD:</strong> 엣지 패턴의 기하학적 복잡도 (1.0~2.0)</li>
                    <li><strong>L:</strong> 패턴의 공간적 분포 특성 (0~1)</li>
                </ul>
                <p style='color: #666; margin-top: 1rem; font-size: 0.9rem;'>
                    <strong>선호 범위 (FD 1.2~1.7)</strong>는 다수의 연구에서 
                    인간이 선호하고 인지적 회복을 촉진하는 것으로 밝혀진 범위입니다.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # 참고 자료
            st.markdown("---")
            st.markdown("### 📚 더 알아보기")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **Fractal Dimension 기초**
                - [Wikipedia - Fractal Dimension](https://en.wikipedia.org/wiki/Fractal_dimension)
                - [Wolfram MathWorld](https://mathworld.wolfram.com/FractalDimension.html)
                - [Box-Counting Method](https://en.wikipedia.org/wiki/Minkowski%E2%80%93Bouligand_dimension)
                """)
            
            with col2:
                st.markdown("""
                **주요 연구**
                - Taylor et al. (2011). Fractal fluency
                - Hagerhall et al. (2015). EEG responses
                - Spehar et al. (2003). Universal aesthetics
                """)
            
            # CSV 다운로드
            st.markdown("---")
            st.markdown("### 📥 결과 다운로드")
            
            csv_data = f"filename,FD,L\n{uploaded_file.name},{FD:.4f},{L:.4f}"
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
    
    df = pd.DataFrame(st.session_state.results_history)
    df = df[['filename', 'FD', 'L', 'timestamp']]
    
    df['FD'] = df['FD'].apply(lambda x: f"{x:.3f}")
    df['L'] = df['L'].apply(lambda x: f"{x:.3f}")
    
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
        - **FD (1.0~2.0)**: 기하학적 복잡도
        - **L (0~1)**: 패턴 불균일성
        - **선호 범위**: FD 1.2~1.7
        """)
    
    st.markdown("---")
    st.markdown("""
    ### ❓ 자주 묻는 질문
    
    **Q: FD 값이 높을수록 좋은 건가요?**  
    A: 아니요. FD 1.2~1.7이 인간이 선호하는 범위입니다. 너무 낮거나 높으면 단조롭거나 복잡합니다.
    
    **Q: L 값은 무엇을 의미하나요?**  
    A: 패턴이 얼마나 균일하게/불규칙하게 배치되어 있는지를 나타냅니다.
    
    **Q: 어떤 값을 선택해야 하나요?**  
    A: 목적에 따라 다릅니다. 편안한 공간은 FD 1.3~1.5, 흥미로운 공간은 FD 1.5~1.7을 추천합니다.
    """)

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; padding: 2rem;'>
    <p>Material Complexity Analyzer</p>
    <p style='font-size: 0.9rem;'>
        Box-Counting Fractal Dimension + Lacunarity Analysis
    </p>
    <p style='font-size: 0.8rem; margin-top: 1rem;'>
        Based on fractal geometry and visual perception research
    </p>
</div>
""", unsafe_allow_html=True)
