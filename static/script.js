// 전역 변수
let currentDiaryData = null;

// DOM이 로드되면 실행
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 앱 초기화
function initializeApp() {
    // 이벤트 리스너 등록
    document.getElementById('uploadForm').addEventListener('submit', handleFormSubmit);
    document.getElementById('useDateAnalysis').addEventListener('change', toggleDateInput);
    
    // 초기 상태 설정
    showWelcomeSection();
}

// 폼 제출 처리
async function handleFormSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const file = formData.get('file');
    const useDateAnalysis = formData.get('use_date_analysis') === 'on';
    const targetDate = formData.get('target_date');
    
    if (!file) {
        showAlert('파일을 선택해주세요.', 'warning');
        return;
    }
    
    // 날짜별 분석이 체크되었는데 날짜가 입력되지 않은 경우
    if (useDateAnalysis && (!targetDate || !targetDate.trim())) {
        showAlert('날짜별 분석을 사용하려면 특정 날짜를 입력해주세요.', 'warning');
        return;
    }
    
    // 로딩 상태 표시
    showLoadingSection();
    
    try {
        const response = await fetch('/auto-diary', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('서버 응답:', result); // 디버깅용 로그
        
        // 응답 구조 확인
        console.log('응답 필드들:', {
            success: result.success,
            diary: result.diary,
            content: result.content,
            emotions: result.emotions,
            date: result.date,
            target_date: result.target_date
        });
        
        if (result.success || result.diary || result.content) {
            console.log('일기 결과 표시 시작');
            displayDiaryResult(result);
        } else {
            console.log('일기 생성 실패');
            showAlert(result.error || '일기 생성에 실패했습니다.', 'danger');
            showWelcomeSection();
        }
        
    } catch (error) {
        console.error('Error:', error);
        showAlert('서버 오류가 발생했습니다. 다시 시도해주세요.', 'danger');
        showWelcomeSection();
    }
}

// 날짜 입력 섹션 토글
function toggleDateInput() {
    const dateAnalysisCheckbox = document.getElementById('useDateAnalysis');
    const dateInputSection = document.getElementById('dateInputSection');
    const targetDateInput = document.getElementById('targetDate');
    
    if (dateAnalysisCheckbox.checked) {
        dateInputSection.style.display = 'block';
        targetDateInput.required = true;
    } else {
        dateInputSection.style.display = 'none';
        targetDateInput.required = false;
        targetDateInput.value = '';
    }
}

// 로딩 섹션 표시
function showLoadingSection() {
    document.getElementById('welcomeSection').style.display = 'none';
    document.getElementById('resultSection').style.display = 'none';
    document.getElementById('loadingSection').style.display = 'block';
}

// 웰컴 섹션 표시
function showWelcomeSection() {
    document.getElementById('loadingSection').style.display = 'none';
    document.getElementById('resultSection').style.display = 'none';
    document.getElementById('welcomeSection').style.display = 'block';
}

// 일기 결과 표시
function displayDiaryResult(result) {
    console.log('displayDiaryResult 호출됨:', result); // 디버깅용 로그
    currentDiaryData = result;
    
    // DOM 요소들 확인
    const diaryDate = document.getElementById('diaryDate');
    const diaryText = document.getElementById('diaryText');
    const loadingSection = document.getElementById('loadingSection');
    const welcomeSection = document.getElementById('welcomeSection');
    const resultSection = document.getElementById('resultSection');
    
    console.log('DOM 요소들:', {
        diaryDate: diaryDate,
        diaryText: diaryText,
        loadingSection: loadingSection,
        welcomeSection: welcomeSection,
        resultSection: resultSection
    });
    
    // 날짜 설정
    if (diaryDate) {
        const dateText = result.date || result.target_date || new Date().toLocaleDateString('ko-KR');
        diaryDate.textContent = dateText;
        console.log('설정된 날짜:', dateText); // 디버깅용 로그
    } else {
        console.error('diaryDate 요소를 찾을 수 없습니다.');
    }
    
    // 일기 내용 설정
    if (diaryText) {
        const contentText = result.diary || result.content || result.summary || '일기 내용을 불러올 수 없습니다.';
        diaryText.textContent = contentText;
        console.log('설정된 내용:', contentText); // 디버깅용 로그
    } else {
        console.error('diaryText 요소를 찾을 수 없습니다.');
    }
    
    // 감정 차트 생성
    console.log('감정 분석 데이터:', result.emotions);
    console.log('웹용 감정 데이터:', result.emotions_web);
    
    // 웹용 감정 데이터가 있으면 사용, 없으면 기본 감정 데이터 사용
    const emotionData = result.emotions_web || result.emotions;
    if (emotionData) {
        createEmotionChart(emotionData);
    } else {
        console.log('감정 분석 데이터가 없습니다.');
    }
    
    // 섹션 표시
    if (loadingSection) {
        loadingSection.style.display = 'none';
        console.log('로딩 섹션 숨김');
    }
    if (welcomeSection) {
        welcomeSection.style.display = 'none';
        console.log('웰컴 섹션 숨김');
    }
    if (resultSection) {
        resultSection.style.display = 'block';
        console.log('결과 섹션이 표시되었습니다.');
    } else {
        console.error('결과 섹션을 찾을 수 없습니다.');
    }
}

// 감정 차트 생성
function createEmotionChart(emotions) {
    console.log('createEmotionChart 호출됨:', emotions);
    
    const chartContainer = document.getElementById('emotionChart');
    
    if (!chartContainer) {
        console.error('감정 차트 컨테이너를 찾을 수 없습니다.');
        return;
    }
    
    // 기존 차트가 있으면 안전하게 제거
    if (window.emotionChart) {
        try {
            if (typeof window.emotionChart.destroy === 'function') {
                window.emotionChart.destroy();
            } else if (window.emotionChart.chart && typeof window.emotionChart.chart.destroy === 'function') {
                window.emotionChart.chart.destroy();
            }
        } catch (error) {
            console.warn('기존 차트 제거 중 오류:', error);
        }
        window.emotionChart = null;
    }
    
    // 기존 canvas 제거
    const existingCanvas = chartContainer.querySelector('canvas');
    if (existingCanvas) {
        existingCanvas.remove();
    }
    
    // 새로운 canvas 생성
    const canvas = document.createElement('canvas');
    canvas.id = 'emotionChartCanvas';
    chartContainer.appendChild(canvas);
    
    console.log('차트 데이터:', emotions);
    
    // Chart.js가 로드되었는지 확인
    if (typeof Chart === 'undefined') {
        console.error('Chart.js가 로드되지 않았습니다.');
        return;
    }
    
    try {
            window.emotionChart = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: ['좋음', '평범함', '나쁨'],
            datasets: [{
                data: [
                    emotions.good || emotions.좋음 || 0,
                    emotions.normal || emotions.평범함 || 0,
                    emotions.bad || emotions.나쁨 || 0
                ],
                    backgroundColor: [
                        '#28a745',  // 좋음 - 초록색
                        '#ffc107',  // 평범함 - 노란색
                        '#dc3545'   // 나쁨 - 빨간색
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                return `${label}: ${value}%`;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
        console.log('차트 생성 성공!');
    } catch (error) {
        console.error('차트 생성 실패:', error);
    }
}

// 일기 다운로드
function downloadDiary() {
    if (!currentDiaryData) {
        showAlert('다운로드할 일기가 없습니다.', 'warning');
        return;
    }
    
    const content = `감성 일기 - ${currentDiaryData.date || new Date().toLocaleDateString('ko-KR')}

${currentDiaryData.diary || currentDiaryData.content || ''}

감정 분석:
- 좋음: ${currentDiaryData.emotions?.good || 0}%
- 평범함: ${currentDiaryData.emotions?.normal || 0}%
- 나쁨: ${currentDiaryData.emotions?.bad || 0}%

생성 시간: ${new Date().toLocaleString('ko-KR')}`;
    
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `감성일기_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// 일기 공유
function shareDiary() {
    if (!currentDiaryData) {
        showAlert('공유할 일기가 없습니다.', 'warning');
        return;
    }
    
    const shareText = `감성 일기 - ${currentDiaryData.date || new Date().toLocaleDateString('ko-KR')}

${currentDiaryData.diary || currentDiaryData.content || ''}

감정 분석: 좋음 ${currentDiaryData.emotions?.good || 0}%, 평범함 ${currentDiaryData.emotions?.normal || 0}%, 나쁨 ${currentDiaryData.emotions?.bad || 0}%`;
    
    if (navigator.share) {
        navigator.share({
            title: '감성 일기',
            text: shareText,
            url: window.location.href
        }).catch(console.error);
    } else {
        // 클립보드에 복사
        navigator.clipboard.writeText(shareText).then(() => {
            showAlert('일기 내용이 클립보드에 복사되었습니다!', 'success');
        }).catch(() => {
            showAlert('클립보드 복사에 실패했습니다.', 'warning');
        });
    }
}

// 알림 표시
function showAlert(message, type = 'info') {
    // 기존 알림 제거
    const existingAlert = document.querySelector('.alert');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    // 새 알림 생성
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // 알림을 페이지 상단에 추가
    const container = document.querySelector('.container-fluid');
    container.insertBefore(alertDiv, container.firstChild);
    
    // 5초 후 자동 제거
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// 파일 드래그 앤 드롭 기능
function setupDragAndDrop() {
    const fileInput = document.getElementById('file');
    const dropZone = document.querySelector('.upload-section');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight(e) {
        dropZone.classList.add('drag-over');
    }
    
    function unhighlight(e) {
        dropZone.classList.remove('drag-over');
    }
    
    dropZone.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            // 파일 선택 이벤트 트리거
            const event = new Event('change', { bubbles: true });
            fileInput.dispatchEvent(event);
        }
    }
}

// 페이지 로드 시 드래그 앤 드롭 설정
document.addEventListener('DOMContentLoaded', setupDragAndDrop); 