"""
정확한 H, C_JS, F 계산 (Bariviera et al. 2025 방법론)

Hilbert Curve + Bandt-Pompe + Information Theory
"""

import numpy as np
from hilbertcurve.hilbertcurve import HilbertCurve
from scipy.special import factorial
import itertools

def hilbert_to_sequence(image_array, size=512):
    """
    2D 이미지를 Hilbert Curve로 1D 시퀀스 변환
    
    Parameters:
    -----------
    image_array : numpy array (grayscale)
    size : int (2^n 크기, 기본 512)
    
    Returns:
    --------
    sequence : 1D numpy array
    """
    # Grayscale 변환 (이미 gray면 그대로)
    if len(image_array.shape) == 3:
        gray = 0.299 * image_array[:,:,0] + 0.587 * image_array[:,:,1] + 0.114 * image_array[:,:,2]
    else:
        gray = image_array
    
    # 512x512 리사이즈
    from PIL import Image
    img_pil = Image.fromarray(gray.astype('uint8'))
    img_pil = img_pil.resize((size, size))
    img_array = np.array(img_pil, dtype=float)
    
    # Hilbert Curve 생성
    n = int(np.log2(size))  # 512 = 2^9
    hilbert = HilbertCurve(n, 2)
    
    # 1D sequence 추출
    sequence = []
    for i in range(size * size):
        coords = hilbert.point_from_distance(i)
        pixel_value = img_array[coords[1], coords[0]]
        sequence.append(pixel_value)
    
    return np.array(sequence)


def ordinal_patterns(sequence, D=5, tau=1):
    """
    Bandt-Pompe ordinal patterns 생성
    
    Parameters:
    -----------
    sequence : 1D array
    D : embedding dimension (패턴 길이)
    tau : time delay
    
    Returns:
    --------
    patterns : list of tuples (각 부분 시퀀스의 순열 패턴)
    pattern_probs : dict {pattern: probability}
    """
    N = len(sequence)
    patterns = []
    
    # 부분 시퀀스 추출 및 패턴 변환
    for t in range(N - (D-1)*tau):
        # 부분 시퀀스
        sub_seq = [sequence[t + i*tau] for i in range(D)]
        
        # 순열 패턴 (argsort)
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
    """
    H (Permutation Entropy) 계산
    
    H[P] = S[P] / ln(D!)
    
    Parameters:
    -----------
    pattern_probs : dict {pattern: probability}
    D : embedding dimension
    normalize : bool (True면 0-1로 정규화)
    
    Returns:
    --------
    H : float (0-1)
    """
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
    """
    C_JS (Statistical Complexity) 계산
    
    C_JS[P] = Q_J[P, P_e] × H[P]
    
    Parameters:
    -----------
    pattern_probs : dict {pattern: probability}
    D : embedding dimension
    
    Returns:
    --------
    C_JS : float (0-1)
    """
    # P_e: 균등 분포
    num_patterns = factorial(D)
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
    
    # Q_0 정규화 상수 (논문 Eq. 6)
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
    """
    F (Fisher Information) 계산
    
    F[P] = F_0 × Σ[√p(j+1) - √p(j)]²
    
    Parameters:
    -----------
    pattern_probs : dict {pattern: probability}
    D : embedding dimension
    
    Returns:
    --------
    F : float (0-1)
    """
    # 모든 가능한 패턴을 Lehmer code 순서로 정렬
    all_patterns = list(itertools.permutations(range(D)))
    
    # Lehmer code로 정렬 (사전순)
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
    
    # F_0 정규화 상수 (논문 Eq. 9)
    # 극단적 케이스 체크
    if np.max(probs) == 1 and np.sum(probs > 0) == 1:
        # 하나의 패턴만 1, 나머지 0
        if np.argmax(probs) in [0, len(probs)-1]:
            F_0 = 1
        else:
            F_0 = 0.5
    else:
        F_0 = 0.5
    
    F = F_0 * F_sum
    
    return F


def measure_complexity_accurate(image_array, D=5, tau=1, size=512):
    """
    정확한 H, C_JS, F 측정 (논문 방법론)
    
    Parameters:
    -----------
    image_array : numpy array (RGB or grayscale)
    D : embedding dimension (기본 5)
    tau : time delay (기본 1)
    size : Hilbert curve 크기 (기본 512)
    
    Returns:
    --------
    H, C, F : float (각각 0-1 범위)
    """
    # Step 1: Hilbert Curve → 1D sequence
    sequence = hilbert_to_sequence(image_array, size)
    
    # Step 2: Ordinal patterns → Probability distribution
    patterns, pattern_probs = ordinal_patterns(sequence, D, tau)
    
    # Step 3: Calculate H, C_JS, F
    H = permutation_entropy(pattern_probs, D, normalize=True)
    C = statistical_complexity(pattern_probs, D)
    F = fisher_information(pattern_probs, D)
    
    return H, C, F


# 테스트 코드
if __name__ == "__main__":
    # 테스트 이미지 생성
    test_image = np.random.randint(0, 256, (512, 512), dtype=np.uint8)
    
    H, C, F = measure_complexity_accurate(test_image)
    
    print(f"H (Permutation Entropy): {H:.4f}")
    print(f"C (Statistical Complexity): {C:.4f}")
    print(f"F (Fisher Information): {F:.4f}")
