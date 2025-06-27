from flask import Flask, render_template, send_from_directory, Response, redirect
import subprocess
import os
import re
from datetime import datetime
import logging

# 로그 설정
logging.basicConfig(
    filename='flask_app.log',  # 로그 파일 이름
    filemode='w',              # 'w'는 덮어쓰기 모드, 'a'는 추가 모드
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Flask 앱 생성
app = Flask(__name__)
DATA_DIR = "data"
DATA_ETC_DIR = os.path.join(DATA_DIR, "etc")

logger = logging.getLogger(__name__)

# Get available dates from existing data files
def get_available_dates():
    dates = set()
    file_pattern = re.compile(r'car_data_(\d{8})\.xlsx')
    
    for filename in os.listdir(DATA_DIR):
        match = file_pattern.match(filename)
        if match:
            dates.add(match.group(1))
            
    return sorted(list(dates), reverse=True)  # Most recent first

@app.route("/")
def index():
    logger.info('메인 페이지 접속')
    today = datetime.now().strftime("%Y%m%d")
    available_dates = get_available_dates()
    return render_template("index.html", date=today, today=today, available_dates=available_dates)

@app.route("/date/<date>")
def show_date(date):
    today = datetime.now().strftime("%Y%m%d")
    available_dates = get_available_dates()
    return render_template("index.html", date=date, today=today, available_dates=available_dates)

@app.route("/run-all")
def run_all():
    logger.info('자동 스크래핑 실행 요청 받음')
    def generate():
        cmds = [
            ["python3", "src/autoscrap.py"],
            ["python3", "src/autoscrap-web.py"],
            ["python3", "src/autoscrap-compare.py"]
        ]
        for cmd in cmds:
            yield f"\n==== Running: {' '.join(cmd)} ====\n"
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in iter(process.stdout.readline, ''):
                yield line
            process.stdout.close()
            process.wait()

        today = datetime.now().strftime("%Y%m%d")
        yield f"\n✅ 전체 완료! 아래에서 결과 다운로드:\n"
        yield f"➡️ /download/car_data_{today}.xlsx\n"
        yield f"➡️ /download/car_data_web_{today}.xlsx\n"
        yield f"➡️ /download/discrepancies_{today}.xlsx\n"

    logger.info('자동 스크래핑 실행 완료')
    return Response(generate(), mimetype='text/plain')

@app.route("/download/<filename>")
def download(filename):
    if "web" in filename or "discrepancies" in filename:
        return send_from_directory(DATA_ETC_DIR, filename, as_attachment=True)
    else:
        return send_from_directory(DATA_DIR, filename, as_attachment=True)

# 애플리케이션 실행 시 로깅
if __name__ == "__main__":
    logger.info('Flask 애플리케이션 시작')
    app.run(host="0.0.0.0", port=8000)
    logger.info('Flask 애플리케이션 종료')
