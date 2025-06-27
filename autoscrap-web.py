import asyncio
import json
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime
import os
import logging
import sys
import importlib.util
from pathlib import Path
import re

compare_file_path = os.path.join(os.path.dirname(__file__), 'autoscrap-compare.py')
if os.path.exists(compare_file_path):
    spec = importlib.util.spec_from_file_location("data_compare", compare_file_path)
    data_compare = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(data_compare)
else:
    print("Warning: autoscrap-compare.py 파일을 찾을 수 없습니다.")
    data_compare = None

# 로깅 설정 개선
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)

def ensure_directories():
    os.makedirs("src", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/etc", exist_ok=True)

def load_urls():
    with open("src/urls-web.json") as f:
        data = json.load(f)
    return data["url"]

async def scrape_all_sections():
    all_results = []
    urls = load_urls()    
    brand_map = {
        0: "01_BMW",
        1: "04_Mini",
        2: "02_MB",
        3: "03_Audi",
        4: "12_Volkswagen",
    }

    for i, url in enumerate(urls):
        results = []
        brand = brand_map.get(i, f"Unknown_{i}")        
        print(f"브랜드 {brand} 스크래핑 시작: {url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--disable-gpu', '--disable-dev-shm-usage', '--no-sandbox'])
            page = await browser.new_page()
            # 페이지 생성 후 이미지, 스타일시트, 폰트 등 불필요한 리소스 차단
            await page.route('**/*.{png,jpg,jpeg,svg,css,woff,woff2}', lambda route: route.abort())
            try:
                await page.goto(url, timeout=60000)
                await page.wait_for_load_state("load")                
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")

                sections = soup.find_all("section", class_="_1vrlmaf2 _1vrlmaf0")
                for section in sections:
                    section_id = section.get("id", "no-id")
                    
                    # 시리즈 이름 추출
                    series_name = section_id  # 기본값으로 section_id 사용
                    section_header = section.select_one("h3.j00ses5")
                    if section_header:
                        header_text_nodes = [text for text in section_header.stripped_strings]
                        
                        if len(header_text_nodes) >= 2:
                            series_name = header_text_nodes[1].strip()
                        elif header_text_nodes:
                            series_name = header_text_nodes[0].strip()
                    
                    # 연식 정보 추출
                    model_year = "25"  # 기본값
                    if section_header:
                        year_span = section_header.select_one("span")
                        if year_span:
                            year_text = year_span.get_text(strip=True)
                            year_match = re.search(r'(\d+)년식', year_text)
                            if year_match:
                                model_year = year_match.group(1)
                            else:
                                year_match = re.search(r'20(\d{2})년식', year_text)
                                if year_match:
                                    model_year = year_match.group(1)

                    rows = section.select("a._15c6uvi5, div._15c6uvi5")
                    for row in rows:
                        try:
                            # 모델명 추출
                            model_name_elem = row.select_one("span._15c6uvi9")
                            if not model_name_elem:
                                continue
                        
                            model_name = model_name_elem.get_text(strip=True)
                            
                            msrp_elem = row.select_one("div._15c6uvi7 span._15c6uvif")
                            msrp = msrp_elem.get_text(strip=True) if msrp_elem else ""
                            
                            discount_elem = row.select_one("span._15c6uvim._15c6uvif")
                            discount = discount_elem.get_text(strip=True) if discount_elem else "0"
                            
                            logging.info(f"추출: {model_name}, 출고가: {msrp}만원, 할인: {discount}만원")
                            
                            results.append({
                                "Brand": brand,
                                "Series": series_name,
                                "MY": model_year,
                                "Model": model_name,
                                "MSRP": msrp,
                                "Off": discount
                            })
                        except Exception as e:
                            logging.error(f"행 데이터 추출 중 오류 발생: {e}")
                            results.append({
                                "Brand": brand,
                                "Series": section_id,
                                "MY": model_year,
                                "Model": "Error",
                                "MSRP": "",
                                "Off": str(e)
                            })
                
                all_results.extend(results)
                print(f"{brand} 스크래핑 완료: {len(results)}개 항목")
            except Exception as e:
                print(f"에러 발생: {e}")
            finally:
                await browser.close()
    df = pd.DataFrame(all_results)
    print(df)
    today = datetime.now().strftime("%Y%m%d")
    file_path = f"data/etc/car_data_web_{today}.xlsx"

    # 이미 파일이 존재하더라도 새 데이터로 덮어쓰기 (기존 데이터는 버림)
    with pd.ExcelWriter(file_path, engine="openpyxl", mode="w") as writer:
        df.to_excel(writer, index=False)

    logging.info(f"💾 {file_path} 저장 완료. 총 {len(df)}행 (기존 데이터 덮어씀).")

if __name__ == "__main__":
    ensure_directories()
    asyncio.run(scrape_all_sections())

    today = datetime.now().strftime("%Y%m%d")
    try:
        if data_compare:
            logging.info("데이터 비교 시작...")
            data_compare.main(today)
            logging.info("데이터 비교 완료")
        else:
            logging.warning("데이터 비교 모듈을 찾을 수 없어 비교를 수행하지 않습니다.")
    except Exception as e:
        logging.error(f"데이터 비교 중 오류 발생: {e}")