import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class ApiService {
  // Render.com 서버 URL (배포 후 실제 URL로 변경)
  static const String baseUrl = 'https://emotion-diary-app.onrender.com';
  
  // 개발용 로컬 서버 (필요시 사용)
  // static const String baseUrl = 'http://10.0.2.2:8000'; // Android 에뮬레이터용
  // static const String baseUrl = 'http://localhost:8000'; // 실제 디바이스용

  // 서버 연결 상태 확인
  static Future<bool> isServerConnected() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/status'),
        headers: {'Content-Type': 'application/json'},
      ).timeout(const Duration(seconds: 10)); // Render.com은 첫 요청이 느릴 수 있으므로 10초로 증가

      return response.statusCode == 200;
    } catch (e) {
      print('서버 연결 실패: $e');
      return false;
    }
  }

  // 일기 생성 API (파인튜닝 모델 사용)
  static Future<Map<String, dynamic>> generateDiary({
    required String kakaoText,
    String? searchLog,
    String? userPrompt,
    bool usePrompt = true,
  }) async {
    try {
      print('🔗 API 호출: generate-diary');
      print('📝 입력 텍스트 길이: ${kakaoText.length}');

      final response = await http.post(
        Uri.parse('$baseUrl/generate-diary'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'kakao_text': kakaoText,
          'search_log': searchLog ?? '없음',
          'user_prompt': userPrompt,
          'use_prompt': usePrompt,
        }),
      ).timeout(const Duration(seconds: 60)); // Render.com은 느릴 수 있으므로 60초로 증가

      print('📡 응답 상태 코드: ${response.statusCode}');

      if (response.statusCode == 200) {
        final decodedBody = utf8.decode(response.bodyBytes);
        final result = jsonDecode(decodedBody);
        print('✅ 일기 생성 성공');
        return result;
      } else {
        print('❌ 일기 생성 실패: ${response.statusCode}');
        print('📄 응답 내용: ${response.body}');
        throw Exception('일기 생성 실패: ${response.statusCode} - ${response.body}');
      }
    } catch (e) {
      print('💥 API 호출 오류: $e');
      throw Exception('API 호출 오류: $e');
    }
  }

  // 파일 업로드를 통한 자동 일기 생성 (파인튜닝 모델 사용)
  static Future<Map<String, dynamic>> autoDiary({
    required File file,
    String? searchLog,
    String? userPrompt,
    bool usePrompt = true,
    bool useDateAnalysis = false,
    String? targetDate,
  }) async {
    try {
      print('🔗 API 호출: auto-diary');
      print('📁 파일 경로: ${file.path}');
      print('📅 날짜별 분석: $useDateAnalysis');
      print('🎯 대상 날짜: $targetDate');

      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/auto-diary'),
      );

      // 파일 추가
      request.files.add(
        await http.MultipartFile.fromPath(
          'file',
          file.path,
        ),
      );

      // 추가 파라미터들
      request.fields['search_log'] = searchLog ?? '없음';
      if (userPrompt != null) {
        request.fields['user_prompt'] = userPrompt;
      }
      request.fields['use_prompt'] = usePrompt.toString();
      request.fields['use_date_analysis'] = useDateAnalysis.toString();
      if (targetDate != null) {
        request.fields['target_date'] = targetDate;
      }

      var streamedResponse = await request.send().timeout(
          const Duration(seconds: 120)); // Render.com은 느릴 수 있으므로 120초로 증가
      var bytes = await streamedResponse.stream.toBytes();
      var responseBody = utf8.decode(bytes);

      print('📡 응답 상태 코드: ${streamedResponse.statusCode}');

      if (streamedResponse.statusCode == 200) {
        final result = jsonDecode(responseBody);
        print('✅ 자동 일기 생성 성공');

        // 파이썬에서 자동으로 emotions 필드를 제공하므로 별도 변환 불필요
        return result;
      } else {
        print('❌ 자동 일기 생성 실패: ${streamedResponse.statusCode}');
        print('📄 응답 내용: $responseBody');
        throw Exception(
            '자동 일기 생성 실패: ${streamedResponse.statusCode} - $responseBody');
      }
    } catch (e) {
      print('💥 파일 업로드 오류: $e');
      throw Exception('파일 업로드 오류: $e');
    }
  }

  // 일관성 테스트 (파인튜닝 모델 품질 검증)
  static Future<Map<String, dynamic>> consistencyTest({
    required File file,
    int testCount = 5,
    String? targetDate,
    bool useDateAnalysis = false,
  }) async {
    try {
      print('🔗 API 호출: consistency-test');
      print('📁 파일 경로: ${file.path}');
      print('🔄 테스트 횟수: $testCount');

      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/consistency-test'),
      );

      // 파일 추가
      request.files.add(
        await http.MultipartFile.fromPath(
          'file',
          file.path,
        ),
      );

      // 추가 파라미터들
      request.fields['test_count'] = testCount.toString();
      request.fields['use_date_analysis'] = useDateAnalysis.toString();
      if (targetDate != null) {
        request.fields['target_date'] = targetDate;
      }

      var streamedResponse = await request.send().timeout(
          const Duration(seconds: 180)); // Render.com은 느릴 수 있으므로 180초로 증가
      var bytes = await streamedResponse.stream.toBytes();
      var responseBody = utf8.decode(bytes);
      final result = jsonDecode(responseBody);

      print('📡 응답 상태 코드: ${streamedResponse.statusCode}');

      if (streamedResponse.statusCode == 200) {
        print('✅ 일관성 테스트 성공');
        return result;
      } else {
        print('❌ 일관성 테스트 실패: ${streamedResponse.statusCode}');
        print('📄 응답 내용: $responseBody');
        throw Exception(
            '일관성 테스트 실패: ${streamedResponse.statusCode} - $responseBody');
      }
    } catch (e) {
      print('💥 일관성 테스트 오류: $e');
      throw Exception('일관성 테스트 오류: $e');
    }
  }

  // 일관성 테스트 정보 조회
  static Future<Map<String, dynamic>> getConsistencyTestInfo() async {
    try {
      print('🔗 API 호출: consistency-test-info');

      final response = await http.get(
        Uri.parse('$baseUrl/consistency-test-info'),
      ).timeout(const Duration(seconds: 15)); // Render.com은 느릴 수 있으므로 15초로 증가

      print('📡 응답 상태 코드: ${response.statusCode}');

      if (response.statusCode == 200) {
        final decodedBody = utf8.decode(response.bodyBytes);
        final result = jsonDecode(decodedBody);
        print('✅ 일관성 테스트 정보 조회 성공');
        return result;
      } else {
        print('❌ 정보 조회 실패: ${response.statusCode}');
        throw Exception('정보 조회 실패: ${response.statusCode}');
      }
    } catch (e) {
      print('💥 정보 조회 오류: $e');
      throw Exception('정보 조회 오류: $e');
    }
  }

  // 날짜별 분석 테스트
  static Future<Map<String, dynamic>> testDateAnalysis() async {
    try {
      print('🔗 API 호출: test-date-analysis');

      final response = await http.get(
        Uri.parse('$baseUrl/test-date-analysis'),
      ).timeout(const Duration(seconds: 15)); // Render.com은 느릴 수 있으므로 15초로 증가

      print('📡 응답 상태 코드: ${response.statusCode}');

      if (response.statusCode == 200) {
        final decodedBody = utf8.decode(response.bodyBytes);
        final result = jsonDecode(decodedBody);
        print('✅ 날짜별 분석 테스트 성공');
        return result;
      } else {
        print('❌ 날짜별 분석 테스트 실패: ${response.statusCode}');
        throw Exception('날짜별 분석 테스트 실패: ${response.statusCode}');
      }
    } catch (e) {
      print('💥 날짜별 분석 테스트 오류: $e');
      throw Exception('날짜별 분석 테스트 오류: $e');
    }
  }

  // Render.com 서버 상태 확인
  static Future<Map<String, dynamic>> checkModelStatus() async {
    try {
      print('🔍 서버 연결 테스트: $baseUrl/api/flutter/status');

      final response = await http.get(
        Uri.parse('$baseUrl/api/flutter/status'),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ).timeout(const Duration(seconds: 15)); // Render.com은 느릴 수 있으므로 15초로 증가

      print('📡 응답 상태 코드: ${response.statusCode}');

      if (response.statusCode == 200) {
        final result = jsonDecode(response.body) as Map<String, dynamic>;
        print('✅ 서버 연결 성공');
        return result;
      } else {
        print('❌ 서버 응답 오류: ${response.statusCode}');
        print('📄 응답 내용: ${response.body}');
        throw Exception('서버 응답 오류: ${response.statusCode}');
      }
    } catch (e) {
      print('💥 서버 연결 실패: $e');
      throw Exception('모델 상태 확인 오류: $e');
    }
  }

  // Render.com 서버 연결 테스트 (첫 요청 지연 대응)
  static Future<bool> testRenderConnection() async {
    try {
      print('🔄 Render.com 서버 연결 테스트 시작...');
      
      // 첫 번째 요청은 느릴 수 있으므로 사용자에게 알림
      print('⏳ 첫 요청은 30초 정도 걸릴 수 있습니다...');
      
      final response = await http.get(
        Uri.parse('$baseUrl/api/status'),
        headers: {'Content-Type': 'application/json'},
      ).timeout(const Duration(seconds: 45)); // 첫 요청을 위해 45초로 설정

      if (response.statusCode == 200) {
        print('✅ Render.com 서버 연결 성공');
        return true;
      } else {
        print('❌ Render.com 서버 응답 오류: ${response.statusCode}');
        return false;
      }
    } catch (e) {
      print('💥 Render.com 서버 연결 실패: $e');
      return false;
    }
  }
} 