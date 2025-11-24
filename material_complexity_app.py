import streamlit as st
import numpy as np
from PIL import Image
import cv2
import pandas as pd
from datetime import datetime
import gc  # 가비지 컬렉션 (메모리 해제용)

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 스타일
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="재질 복잡도 측정기 (Material Complexity Analyzer)",
    page_icon="🔬",
    layout="wide"
)

# 세션 상태 초기화 (측정 기록 저장용)
if 'results_history' not in st.session_state:
    st.session_state.results_history = []

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
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card-fd {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
    }
    .metric-card-l {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    .metric-value {
        font-size: 3rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 1.2rem;
        font-weight: 500;
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
        font-weight: 600;
        text-align: center;
    }
    .interpretation-low { background-color: #e8f5e9; color: #2e7d32; }
    .interpretation-medium { background-color: #fff3e0; color: #e65100; }
    .interpretation-high { background-color: #fce4ec; color: #c2185b; }
    .interpretation-preferred { 
        background-color: #e3f2fd; 
        color: #1565c0; 
        border: 2px solid #2196f3;
    }
    .info-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #6c757d;
        color: #333;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        padding: 0.75rem;
        border-radius: 8px;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #155a8a;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 핵심 알고리즘 (Numpy Vectorization 적용)
# -----------------------------------------------------------------------------

def resize_for_memory(image, max_dim=1024):
    """
    메모리 최적화를 위해 이미지 크기 조정
    가로/세로 중 긴 쪽을 max_dim(기본 1024px)으로 맞춤
    """
    width, height = image.size
    if max(width, height) > max_dim:
        ratio = max_dim / max(width, height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        # LANCZOS 필터 사용 (품질 유지하면서 리사이징)
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return image

def box_count(image, k):
    """
    Numpy Vectorization을 이용한 고속 박스 카운팅
    """
    S = image.shape
    h_trim = S[0] // k * k
    w_trim = S[1] // k * k
    
    if h_trim == 0 or w_trim == 0:
        return 0
    
    img_trim = image[:h_trim, :w_trim]
    reshaped = img_trim.reshape(h_trim//k, k, w_trim//k, k)
    has_edge = np.max(reshaped, axis=(1, 3)) > 0
    
    return np.sum(has_edge)

def fractal_dimension(image_array):
    """
    프랙탈 차원 계산 (Box-Counting Method)
    """
    if len(image_array.shape) == 3:
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_array
    
    edges = cv2.Canny(gray, 50, 150)
    
    box_sizes = np.array([2, 4, 8, 16, 32, 64], dtype=float)
    counts = []
    
    for size in box_sizes:
        count = box_count(edges, int(size))
        counts.append(count)
    
    counts = np.array(counts, dtype=float)
    valid = counts > 0
    box_sizes_valid = box_sizes[valid]
    counts_valid = counts[valid]
    
    if len(counts_valid) < 2:
        return 1.0, 0.0
    
    log_sizes = np.log(box_sizes_valid)
    log_counts = np.log(counts_valid)
    
    coeffs = np.polyfit(log_sizes, log_counts, 1)
    slope = coeffs[0]
    intercept = coeffs[1]
    
    log_counts_pred = slope * log_sizes + intercept
    ss_res = np.sum((log_counts - log_counts_pred) ** 2)
    ss_tot = np.sum((log_counts - np.mean(log_counts)) ** 2)
    
    if ss_tot > 0:
        r_squared = 1 - (ss_res / ss_tot)
    else:
        r_squared = 0.0
    
    FD = -slope
    FD = np.clip(FD, 1.0, 2.0)
    
    return FD, r_squared

def lacunarity(image_array):
    """
    Lacunarity 계산 (Gliding Box Method - Approximation)
    """
    if len(image_array.shape) == 3:
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_array
    
    box_size = 32
    stride = 8 
    h, w = gray.shape
    
    masses = []
    for i in range(0, h-box_size, stride):
        for j in range(0, w-box_size, stride):
            box = gray[i:i+box_size, j:j+box_size]
            mass = np.sum(box > 128)
            masses.append(mass)
    
    masses = np.array(masses)
    
    if len(masses) == 0 or np.mean(masses) == 0:
        return 0.0
    
    L = (np.std(masses) / np.mean(masses)) ** 2
    L_normalized = min(L / 2.0, 1.0)
    
    return L_normalized

def measure_complexity(image_array):
    FD, r_squared = fractal_dimension(image_array)
    L = lacunarity(image_array)
    return FD, L, r_squared

# -----------------------------------------------------------------------------
# 3. 결과 해석 로직
# -----------------------------------------------------------------------------

def interpret_fd(value):
    if value < 1.2:
        return "단순 (Simple)", "단조로운 패턴, 인지적 자극 낮음", "low"
    elif value < 1.4:
        return "선호 (Preferred - Calm)", "편안함을 주는 최적의 복잡도", "preferred"
    elif value < 1.7:
        return "선호 (Preferred - Stimulating)", "시각적 흥미를 유발하는 적정 복잡도", "preferred"
    elif value < 1.8:
        return "복잡 (High)", "정보량이 많음, 주의 집중 필요", "medium"
    else:
        return "매우 복잡 (Very High)", "시각적 피로 유발 가능성", "high"

def interpret_l(value):
    if value < 0.2:
        return "균일 (Homogeneous)", "반복적이고 예측 가능한 패턴", "low"
    elif value < 0.5:
        return "중간 (Heterogeneous)", "적당한 변화가 있는 패턴", "medium"
    else:
        return "불균일 (Clumped)", "불규칙하고 뭉쳐있는 패턴", "high"

# -----------------------------------------------------------------------------
# 4. UI 구성
# -----------------------------------------------------------------------------

st.markdown('<div class="main-header">🔬 Material Complexity Analyzer</div>', unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #666; margin-bottom: 2rem;'>
    <strong>Box-Counting Fractal Dimension</strong> & <strong>Lacunarity</strong> Analysis<br>
    메모리 최적화 모드: 이미지를 자동으로 최적 크기(Max 1024px)로 조정하여 분석합니다.
</div>
""", unsafe_allow_html=True)

# 사이드바: 기록 및 정보
with st.sidebar:
    st.markdown("### 📊 측정 히스토리")
    
    if st.session_state.results_history:
        if st.button("🗑️ 기록 초기화"):
            st.session_state.results_history = []
            st.rerun()
            
        history_df = pd.DataFrame(st.session_state.results_history)
        for i, row in history_df.iloc[::-1].iterrows():
            with st.expander(f"{row['filename'][:15]}..."):
                st.write(f"**FD:** {row['FD']:.3f}")
                st.write(f"**L:** {row['L']:.3f}")
                st.caption(f"신뢰도(R²): {row['r_squared']:.3f}")
    else:
        st.info("측정된 기록이 없습니다.")
    
    st.divider()
    st.markdown("### ℹ️ 알고리즘 정보")
    st.caption("""
    **Method:** Box-Counting
    **Optimization:** - Numpy Vectorization
    - Auto-Resizing (Max 1024px)
    - Memory Garbage Collection
    """)

# 메인: 파일 업로드 (다중 파일 지원으로 변경)
uploaded_files = st.file_uploader(
    "재질 이미지 업로드 (JPG, PNG) - 여러 장 선택 가능", 
    type=['jpg', 'jpeg', 'png'], 
    accept_multiple_files=True  # 다중 파일 업로드 허용
)

if uploaded_files:
    # 안내 메시지
    st.info(f"총 {len(uploaded_files)}개의 파일이 선택되었습니다. '분석 시작' 버튼을 누르면 순차적으로 분석합니다.")
    
    # 첫 번째 이미지만 미리보기로 보여줌 (메모리 절약)
    first_image = Image.open(uploaded_files[0])
    # 미리보기용 이미지도 작게 줄여서 출력
    first_image_small = resize_for_memory(first_image, max_dim=500)
    
    col1, col2 = st.columns([1, 1.5])
    with col1:
        st.image(first_image_small, caption=f"첫 번째 이미지 미리보기: {uploaded_files[0].name}", use_container_width=True)
        st.caption("⚠️ 메모리 보호를 위해 첫 번째 이미지만 미리보기를 제공합니다.")

    with col2:
        if st.button("🚀 전체 이미지 분석 시작", type="primary", use_container_width=True):
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 마지막 분석 결과 변수 (화면 표시용)
            last_result = None
            
            for idx, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"분석 중 ({idx+1}/{len(uploaded_files)}): {uploaded_file.name}...")
                
                try:
                    # 1. 이미지 로드 및 리사이징 (메모리 핵심!)
                    image = Image.open(uploaded_file)
                    image = resize_for_memory(image, max_dim=1024) # 1024px로 리사이징
                    image_array = np.array(image)
                    
                    # 2. 분석 수행
                    FD, L, r_squared = measure_complexity(image_array)
                    
                    # 3. 결과 저장
                    st.session_state.results_history.append({
                        'filename': uploaded_file.name,
                        'FD': FD, 'L': L, 'r_squared': r_squared,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    # 마지막 결과 저장 (루프 끝나고 보여주기 위함)
                    last_result = (FD, L, r_squared, uploaded_file.name)
                    
                    # 4. 메모리 정리 (핵심!)
                    del image
                    del image_array
                    gc.collect() # 강제 메모리 해제
                    
                except Exception as e:
                    st.error(f"{uploaded_file.name} 처리 중 오류 발생: {e}")
                
                # 진행률 업데이트
                progress_bar.progress((idx + 1) / len(uploaded_files))
            
            status_text.text("✅ 모든 분석이 완료되었습니다!")
            
            # 마지막 분석 결과 카드 표시
            if last_result:
                FD, L, r_squared, fname = last_result
                fd_level, fd_desc, fd_class = interpret_fd(FD)
                l_level, l_desc, l_class = interpret_l(L)
                
                st.markdown("---")
                st.markdown(f"### 🏁 마지막 분석 결과 ({fname})")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"""
                    <div class="metric-card metric-card-fd">
                        <div class="metric-label">Fractal Dimension (FD)</div>
                        <div class="metric-value">{FD:.3f}</div>
                        <div class="metric-desc">기하학적 복잡도</div>
                    </div>
                    <div class="interpretation interpretation-{fd_class}">
                        {fd_level}<br><span style='font-size:0.9rem; font-weight:normal'>{fd_desc}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                with c2:
                    st.markdown(f"""
                    <div class="metric-card metric-card-l">
                        <div class="metric-label">Lacunarity (L)</div>
                        <div class="metric-value">{L:.3f}</div>
                        <div class="metric-desc">패턴 불균일성</div>
                    </div>
                    <div class="interpretation interpretation-{l_class}">
                        {l_level}<br><span style='font-size:0.9rem; font-weight:normal'>{l_desc}</span>
                    </div>
                    """, unsafe_allow_html=True)

# 하단: 전체 데이터 테이블 및 다운로드
if st.session_state.results_history:
    st.divider()
    st.markdown("### 📋 전체 분석 결과")
    df = pd.DataFrame(st.session_state.results_history)
    st.dataframe(
        df[['filename', 'FD', 'L', 'r_squared', 'timestamp']], 
        use_container_width=True,
        column_config={
            "FD": st.column_config.NumberColumn(format="%.3f"),
            "L": st.column_config.NumberColumn(format="%.3f"),
            "r_squared": st.column_config.NumberColumn(label="R² (신뢰도)", format="%.3f"),
        }
    )
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 CSV로 다운로드",
        csv,
        "complexity_analysis.csv",
        "text/csv",
        key='download-csv'
    )
