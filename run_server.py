#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from main import create_app

app = create_app()
print("\n" + "="*60)
print("🚀 주식 분석 시스템 웹 서버 시작")
print("="*60)
print("📍 접속 주소: http://localhost:8000")
print("⚙️  Debug 모드: ON")
print("📊 데이터: 삼성전자 (005930)")
print("="*60 + "\n")
app.run(debug=True, host='127.0.0.1', port=8000)
