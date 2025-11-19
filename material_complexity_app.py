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
