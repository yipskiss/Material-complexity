# 🎨 재질 복잡도 측정기 (Material Complexity Analyzer)

재질 이미지의 **프랙탈 차원(FD)**과 **불균일성(L)**을 측정하는 웹 애플리케이션입니다.

---

## 📊 측정 지표

### FD (Fractal Dimension) - 기하학적 복잡도
**범위**: 1.0 ~ 2.0

| 값 | 의미 | 특성 |
|----|------|------|
| 1.0~1.2 | 매우 단순 | 단색, 단순 격자 |
| **1.2~1.4** | **선호 범위 (하)** | 편안함, 인지적 회복 |
| **1.4~1.7** | **선호 범위 (상)** | 흥미로움, 시각적 매력 |
| 1.7~2.0 | 복잡함 | 복잡한 패턴 |

💡 **선호 범위 (1.2~1.7)**는 다수의 연구에서 인간이 선호하고 인지적 회복을 촉진하는 것으로 입증된 범위입니다.

### L (Lacunarity) - 패턴 불균일성
**범위**: 0 ~ 1

| 값 | 의미 | 특성 |
|----|------|------|
| 0.0~0.3 | 균일함 | 규칙적 반복 패턴 |
| 0.3~0.6 | 중간 | 중간 불균일 |
| 0.6~1.0 | 불균일함 | 불규칙 배치 |

💡 같은 FD를 가져도 L이 다르면 다른 시각적 특성을 나타냅니다.

---

## 🔬 이론적 배경

### Fractal Dimension과 시각적 지각

프랙탈 차원은 패턴의 기하학적 복잡도를 측정하는 지표로, 시각적 지각 및 심리적 반응과 밀접한 관련이 있습니다.

#### 중간 범위 FD 선호 (1.2~1.7)

다수의 연구에서 인간이 중간 범위 프랙탈을 선호한다는 것이 입증되었습니다:

- **Taylor et al. (2011)**: 중간 범위 프랙탈 노출 시 긍정적 생리적 반응
- **Hagerhall et al. (2015)**: FD ≈ 1.3에서 최강 이완 및 주의 집중 (EEG 연구)
- **Spehar et al. (2003)**: 문화권 무관한 보편적 선호

#### Fractal Fluency Theory

**Taylor & Spehar (2016)**가 제안한 이론으로, 인간의 시각 시스템이 중간 범위 프랙탈을 효율적으로 처리하도록 진화했다고 설명합니다. 자연에서 중간 FD 프랙탈이 자주 나타나며, 이에 대한 진화적 노출이 시각적 유창성을 형성했다고 봅니다.

---

## 🚀 빠른 시작

### 로컬 실행

```bash
# 저장소 클론
git clone https://github.com/your-username/material-complexity.git
cd material-complexity

# 패키지 설치
pip install -r requirements.txt

# 실행
streamlit run material_complexity_app.py
```

브라우저가 자동으로 열립니다 (http://localhost:8501)

### Streamlit Cloud 배포

1. GitHub 저장소 생성 및 푸시
2. https://streamlit.io/cloud 접속
3. "New app" → GitHub 저장소 연결
4. `material_complexity_app.py` 선택
5. Deploy!

배포 후 링크를 공유하면 누구나 사용 가능합니다.

---

## 📖 사용 방법

1. 이미지 업로드 (JPG, PNG)
2. "🔍 복잡도 측정하기" 클릭
3. 1-2초 후 결과 확인
4. 사이드바에서 측정 기록 확인
5. 필요시 CSV 다운로드

---

## 📚 더 알아보기

### Fractal Dimension 기초

- [Wikipedia - Fractal Dimension](https://en.wikipedia.org/wiki/Fractal_dimension)
- [Wolfram MathWorld - Fractal Dimension](https://mathworld.wolfram.com/FractalDimension.html)
- [Box-Counting Method](https://en.wikipedia.org/wiki/Minkowski%E2%80%93Bouligand_dimension)
- [Lacunarity](https://en.wikipedia.org/wiki/Lacunarity)

### 주요 연구 논문

**프랙탈과 시각 선호**

[1] Spehar, B., Clifford, C. W., Newell, B. R., & Taylor, R. P. (2003). Universal aesthetic of fractals. *Computers & Graphics*, 27(5), 813-820.

[2] Taylor, R. P., Spehar, B., Van Donkelaar, P., & Hagerhall, C. M. (2011). Perceptual and physiological responses to Jackson Pollock's fractals. *Frontiers in Human Neuroscience*, 5, 60.

[3] Forsythe, A., Nadal, M., Sheehy, N., Cela-Conde, C. J., & Sawey, M. (2011). Predicting beauty: Fractal dimension and visual complexity in art. *British Journal of Psychology*, 102(1), 49-70.

**생리적 반응**

[4] Hägerhäll, C. M., Laike, T., Küller, M., Marcheschi, E., Boydston, C., & Taylor, R. P. (2015). Human physiological benefits of viewing nature: EEG responses to exact and statistical fractal patterns. *Nonlinear Dynamics, Psychology, and Life Sciences*, 19(1), 1-12.

[5] Hagerhall, C. M., Purcell, T., & Taylor, R. (2004). Fractal dimension of landscape silhouette outlines as a predictor of landscape preference. *Journal of Environmental Psychology*, 24(2), 247-255.

**Fractal Fluency Theory**

[6] Taylor, R. P., & Spehar, B. (2016). Fractal fluency: An intimate relationship between the brain and processing of fractal stimuli. In *The Fractal Geometry of the Brain* (pp. 485-496). Springer.

[7] Aks, D. J., & Sprott, J. C. (1996). Quantifying aesthetic preference for chaotic patterns. *Empirical Studies of the Arts*, 14(1), 1-16.

**인지적 회복**

[8] Kaplan, R., & Kaplan, S. (1989). *The experience of nature: A psychological perspective*. Cambridge University Press.

---

## 🔬 측정 방법

### Box-Counting Method

프랙탈 차원은 **Box-Counting Method**로 계산됩니다:

```
FD = - lim (log N(ε) / log ε)
      ε→0

N(ε): 크기 ε인 박스로 패턴을 덮는 데 필요한 박스 수
```

**과정:**
1. 이미지를 Grayscale로 변환
2. Canny Edge Detection 적용
3. 여러 크기의 박스로 엣지 카운팅
4. log-log 회귀로 FD 계산

### Lacunarity

패턴의 공간적 분포를 측정:

```
L = (σ / μ)²

σ: 박스별 mass의 표준편차
μ: 평균 mass
```

---

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **Image Processing**: OpenCV, PIL
- **Computation**: NumPy
- **Method**: Box-Counting Fractal Dimension
- **Deployment**: Streamlit Cloud

---

## 📋 Requirements

```
streamlit>=1.28.0
numpy>=1.24.0
opencv-python-headless>=4.8.0
Pillow>=10.0.0
pandas>=2.0.0
```

💡 **중요**: Streamlit Cloud 배포 시 `opencv-python-headless`를 사용하세요 (GUI 불필요)

---

## ❓ FAQ

**Q: FD 값이 높을수록 좋은가요?**  
A: 아니요. FD 1.2~1.7이 선호 범위입니다. 너무 낮으면 단조롭고, 너무 높으면 복잡합니다.

**Q: 어떤 FD 값을 선택해야 하나요?**  
A: 편안한 공간은 FD 1.3~1.5, 흥미로운 공간은 FD 1.5~1.7을 추천합니다.

**Q: L 값은 무엇을 의미하나요?**  
A: 패턴이 얼마나 균일하게/불규칙하게 배치되어 있는지를 나타냅니다.

**Q: 계산이 오래 걸리나요?**  
A: 1-2초 내에 완료됩니다.

---

## 🐛 문제 해결

### Streamlit Cloud 배포 오류

**ImportError: cv2**
```
해결: requirements.txt에 opencv-python-headless 사용
(opencv-python → opencv-python-headless)
```

**ModuleNotFoundError**
```bash
# 로컬에서 테스트
pip install -r requirements.txt
streamlit run material_complexity_app.py
```

**배포 후 앱이 안 열림**
```
1. GitHub 저장소가 public인지 확인
2. requirements.txt 파일명 정확한지 확인
3. Streamlit Cloud 로그 확인 (Manage app)
```

---

## 📊 성능

- **계산 시간**: 1-2초/이미지
- **메모리 사용**: ~50MB
- **지원 크기**: 최대 4096×4096

---

## 📞 문의

- **Email**: your.email@example.com
- **GitHub**: [@your-username](https://github.com/your-username)

---

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

---

## 🙏 감사

- **Richard P. Taylor**: Fractal Fluency Theory
- **Caroline M. Hagerhall**: EEG Studies on Fractals
- **Branka Spehar**: Universal Aesthetics Research

---

**Made with ❤️ for better material design**
