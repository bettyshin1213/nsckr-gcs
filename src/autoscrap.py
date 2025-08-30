import asyncio
import os
import json
import pandas as pd
import re
import logging
import sys
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def ensure_directories():
    os.makedirs("src", exist_ok=True)
    os.makedirs("data", exist_ok=True)

def load_urls():
    with open("src/urls.json") as f:
        data = json.load(f)
    return data["url"]

def load_existing_data():
    try:
        df = pd.read_excel("car_data.xlsx")
        return df
    except FileNotFoundError:
        df = pd.DataFrame(
            columns=[
                "Year", "Month", "Date", "Brand", "MY",
                "Series", "Fuel Type", "Model (adjusted)",
                "MSRP", "Cash_off", "Finance_off"
            ]
        )
        return df

def save_to_excel(new_data, append=False):
    today = datetime.now().strftime("%Y%m%d")
    file_path = f"data/car_data_{today}.xlsx"
    columns = [
        "Year", "Month", "Date", "Brand", "MY",
        "Series", "Fuel Type", "Model (adjusted)",
        "MSRP", "Cash_off", "Finance_off"
    ]
    
    new_df = pd.DataFrame(new_data, columns=columns)
    
    # 이미 파일이 존재하고 append 모드라면 기존 데이터에 추가
    if append and os.path.exists(file_path):
        try:
            existing_df = pd.read_excel(file_path)
            updated_df = pd.concat([existing_df, new_df], ignore_index=True)
            
            with pd.ExcelWriter(file_path, engine="openpyxl", mode="w") as writer:
                updated_df.to_excel(writer, index=False)
                
            logging.info(f"💾 {file_path}에 {len(new_df)}행 추가됨. 총 {len(updated_df)}행.")
            return
        except Exception as e:
            logging.error(f"❌ 기존 파일 읽기/추가 실패, 덮어쓰기로 진행합니다: {e}")
    
    # 첫 실행이거나 append 모드가 아니면 덮어쓰기
    with pd.ExcelWriter(file_path, engine="openpyxl", mode="w") as writer:
        new_df.to_excel(writer, index=False)
    
    logging.info(f"💾 {file_path} 저장 완료. 총 {len(new_df)}행.")

def fuel_type(x):
    if "휘발유" in x:
        return "P"
    elif "경유" in x:
        return "D"
    elif "전기" in x:
        return "BEV"
    elif "플러그인 하이브리드" in x:
        return "PHEV"
    else:
        return "None"

async def get_car_series(page, brand, is_first_brand=False):
    await page.wait_for_load_state("load")
    content = await page.content()
    soup = BeautifulSoup(content, "html.parser")

    elements = soup.find_all(
        class_="css-175oi2r r-1i6wzkk r-lrvibr r-1loqt21 r-1otgn73 r-1awozwy r-18u37iz r-1wtj0ep r-117bsoe r-11wrixw r-61z16t r-1x0uki6 r-1mdbw0j r-1hfyk0a r-1qfoi16 r-wk8lta r-13qz1uu"
    )
    if not elements:
        logging.warning(f"{brand} 시리즈 요소를 찾지 못했습니다.")
        return []

    today = datetime.now()
    all_series_data = []  # 모든 시리즈 데이터를 저장할 리스트

    for element in elements:
        try:
            car_series = element.find(
                "div",
                class_="css-146c3p1 r-1jstmqa r-litx2b r-1b43r93 r-icto9i r-14yzgew r-p76n7o r-13wfysu r-1a2p6p6",
            ).get_text(strip=True)
        except Exception:
            continue

        logging.info(f"시리즈 탐색 중: {car_series}")

        existing_data = load_existing_data()
        

        if not existing_data[
            (existing_data["Year"] == today.year)
            & (existing_data["Month"] == today.month)
            & (existing_data["Date"] == today.day)
            & (existing_data["Series"] == car_series)
        ].empty:
            logging.info(f"⏩ {car_series} 이미 수집됨. 스킵.")
            continue

        # 각 시리즈 데이터 수집
        series_data = await get_car_info(page, car_series, brand)
        if series_data:
            logging.info(f"✅ {car_series} 수집 완료, {len(series_data)}개 항목 수집")
            all_series_data.extend(series_data)  # 전체 데이터 리스트에 추가
            
            # 시리즈 수집 후 바로 저장 (첫 번째 브랜드의 첫 번째 시리즈는 덮어쓰기, 나머지는 추가)
            append_mode = not (is_first_brand and len(all_series_data) == len(series_data))
            save_to_excel(series_data, append=append_mode)
            logging.info(f"💾 {car_series} 데이터 {len(series_data)}개 항목 저장 완료")
        else:
            logging.warning(f"⚠️ {car_series} 수집된 데이터 없음")

        await page.wait_for_load_state("load")

    return all_series_data

async def get_car_info(page, car_series, brand):
    try:
        series_locator = page.locator(f"text={car_series}").first
        await series_locator.click()
        await page.wait_for_load_state("load")

        # 브랜드 페이지 iframe 접근
        if "5" in car_series:
            elements_locator = page.locator("div.sc-80108d2f-0.hlytKE")
        else: 
            brand_iframe_locator = page.frame_locator("iframe[src*='https://cd.getcha.kr/brand/']")
            elements_locator = brand_iframe_locator.locator("div.sc-80108d2f-0.hlytKE")

        await elements_locator.first.wait_for(timeout=3000)

        count = await elements_locator.count()
        if count == 0:
            logging.warning(f"⚠️ 할인되는 {car_series} 모델 없음. 다음 시리즈로 이동.")
            return []

        series_car_data = []

        for i in range(count):
            try:
                el = elements_locator.nth(i)
                await el.scroll_into_view_if_needed()
                await page.wait_for_load_state("load")

                # iframe 전체 HTML 파싱
                brand_frame = next((f for f in page.frames if "https://cd.getcha.kr/brand/" in f.url), None)
                if not brand_frame:
                    raise Exception("❌ 브랜드 iframe 로드 실패")

                content = await brand_frame.content()
                soup = BeautifulSoup(content, "html.parser")
                
                # DOM 트리 순회 대신 직접 선택
                car_model_tags = []
                all_h5s = soup.select("h5.sc-850306bd-6.DcjFc")
                for h5 in all_h5s:
                    parent_div = h5.find_parent("div", class_="sc-80108d2f-0")
                    if parent_div and "hlytKE" in parent_div["class"] and "kwqkHl" not in parent_div["class"]:
                        car_model_tags.append(h5)

                if i >= len(car_model_tags):
                    raise Exception("❌ car_model 엘리먼트 부족")

                car_model_tag = car_model_tags[i]
                car_model = car_model_tag.get_text(strip=True)

                # 가장 가까운 부모 블록 기준으로 검색
                fuel_parent_block = car_model_tag.find_parent("div", class_="sc-84b91bcb-0 fscxQt")
                year_parent_block = car_model_tag.find_parent("div", class_="sc-16e7f35c-0 iTBJvM")

                car_year_tag = year_parent_block.select_one("div.sc-16e7f35c-1.bEkQLM h4.sc-850306bd-5.iXDDjz")
                car_year = car_year_tag.get_text(strip=True)[2:4] if car_year_tag else "00"

                car_fuel_tag = fuel_parent_block.select_one("div.sc-84b91bcb-1.dpHZpA h6.sc-850306bd-8.bcvqMy")
                car_fuel = fuel_type(car_fuel_tag.get_text(strip=True)) if car_fuel_tag else "Unknown"


                logging.info(f"{car_series} - {car_model} ({car_year}) {car_fuel}")
                await el.click()
                await page.wait_for_load_state("domcontentloaded")

                model_data = await get_car_price(page, car_model, car_series, car_year, car_fuel, brand)
                if model_data:
                    series_car_data.append(model_data)

            except Exception as e:
                logging.warning(f"⚠️ {car_series} 모델 {i+1}/{count} 처리 실패: {e}")

            finally:
                try:
                    if not page.is_closed():
                        await page.go_back()
                        await page.wait_for_load_state("load")
                except Exception as e:
                    logging.warning(f"⚠️ 뒤로가기 실패: {e}")
        await page.go_back()
        return series_car_data

    except PlaywrightTimeoutError:
        logging.error(f"❌ {car_series} 모델 클릭 실패 또는 요소 로드 실패")
        try:
            if not page.is_closed():
                await page.go_back()
                await page.wait_for_load_state("load")
        except:
            pass
        return []


async def get_car_price(frame, car_model, car_series, car_year, car_fuel, brand):
    try:
        await frame.wait_for_selector("iframe[src*='car-detail']", timeout=10000)
        await frame.wait_for_load_state("load")

        detail_frame = None
        for f in frame.frames:
            try:
                el = await f.frame_element()
                src = await el.get_attribute("src")
                if src and "car-detail" in src:
                    detail_frame = f
                    break
            except:
                continue

        if not detail_frame:
            raise Exception("❌ car-detail iframe을 src 기반으로 찾을 수 없음")

        await detail_frame.wait_for_selector("div.sc-68368f62-0.gfdAnO", timeout=6000)
        content = await detail_frame.content()
        soup = BeautifulSoup(content, "html.parser")

        msrp_element = soup.select_one("#cardetail_container > div.sc-68368f62-0.gfdAnO > div > div:nth-child(1) > div")
        cash_off_element = soup.select_one("#cardetail_container > div.sc-68368f62-0.gfdAnO > div > div:nth-child(2) > em")
        finance_off_element = soup.select_one("#cardetail_container > div.sc-68368f62-0.gfdAnO > div > div:nth-child(3) > em")

        msrp = msrp_element.get_text(strip=True).replace("만원", "") if msrp_element else "N/A"
        cash_off = re.search(r"([0-9,]+)만원", cash_off_element.get_text(strip=True)).group(1).replace(",", "") if cash_off_element else "0"
        finance_off = re.search(r"([0-9,]+)만원", finance_off_element.get_text(strip=True)).group(1).replace(",", "") if finance_off_element else "0"

        cash_off = f"{int(cash_off):,}"
        finance_off = f"{int(finance_off):,}"

        logging.info(f"가격: {msrp}만원, 현금할인: {cash_off}만원, 금융할인: {finance_off}만원")

        if cash_off != "0" or finance_off != "0":
            return [
                datetime.now().year,
                datetime.now().month,
                datetime.now().day,
                brand,
                car_year,
                car_series,
                car_fuel,
                car_model,
                msrp,
                cash_off,
                finance_off,
            ]
    except Exception as e:
        logging.error(f"❌ {car_model} 가격 파싱 실패: {e}")
    return None

def find_parent_with_class(element, class_name):
    parent = element.parent
    while parent:
        if parent.name == "div" and class_name in parent.get("class", []):
            return parent
        parent = parent.parent
    return None

async def main():
    ensure_directories()
    url = load_urls()
    brand_map = {
        1: "01_BMW",
        2: "04_Mini",
        3: "02_MB",
        4: "03_Audi",
        5: "12_Volkswagen",
    }

    all_data = []
    first_brand = True

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--disable-gpu', '--disable-dev-shm-usage', '--no-sandbox'])
        context = await browser.new_context()

        for i in range(1, 6):
            brand = brand_map[i]
            max_retries = 5  # 최대 재시도 횟수
            retries = 0
            brand_data = []
            
            while retries < max_retries and len(brand_data) == 0:
                if retries > 0:
                    logging.warning(f"⚠️ {brand} 데이터 수집 실패, {retries}번째 재시도 중...")
                    await asyncio.sleep(3)  # 재시도 전 잠시 대기
                
                page = await context.new_page()
                # 페이지 생성 후 이미지, 스타일시트, 폰트 등 불필요한 리소스 차단
                await page.route('**/*.{png,jpg,jpeg,svg,css,woff,woff2}', lambda route: route.abort())
                try:
                    await page.goto(url[i], timeout=600000)
                    await page.wait_for_load_state("load")
                    
                    # BMW 브랜드는 더 오래 기다림
                    if i == 1:  # BMW
                        await asyncio.sleep(5)
                    else:
                        await asyncio.sleep(3)
                    
                    logging.info(f"\n====== 브랜드 시작: {brand} ({retries+1}번째 시도) ======")
                    
                    # 브랜드별 데이터 수집 (첫 번째 브랜드는 is_first_brand=True로 전달)
                    brand_data = await get_car_series(page, brand, is_first_brand=first_brand)
                    
                    if len(brand_data) > 0:
                        logging.info(f"✅ 브랜드 {brand} 데이터 {len(brand_data)}개 수집 완료")
                        all_data.extend(brand_data)
                        break  # 데이터가 수집되었으면 재시도 루프 종료
                    else:
                        logging.warning(f"⚠️ {brand} 데이터 0개 수집됨, 재시도 필요")
                        retries += 1
                        
                except Exception as e:
                    logging.error(f"❌ {brand} 오류 발생: {e}")
                    retries += 1
                finally:
                    await page.close()
            
            if len(brand_data) == 0:
                logging.error(f"❌ {brand} 데이터 수집 최종 실패. 다음 브랜드로 진행합니다.")
            
            first_brand = False  # 첫 번째 브랜드 처리 후 플래그 변경

        await browser.close()

    logging.info(f"💾 전체 데이터 {len(all_data)}개 항목 수집 완료")

    # autoscrap-web.py 실행
    logging.info("\n=== autoscrap.py 완료. autoscrap-web.py 실행 중... ===")
    try:
        # 하위 프로세스로 autoscrap-web.py 실행
        import subprocess
        web_script_path = os.path.join(os.path.dirname(__file__), 'autoscrap-web.py')
        if os.path.exists(web_script_path):
            subprocess.run([sys.executable, web_script_path], check=True)
            logging.info("✅ autoscrap-web.py 실행 완료")
        else:
            logging.error("❌ autoscrap-web.py 파일을 찾을 수 없습니다.")
    except Exception as e:
        logging.error(f"❌ autoscrap-web.py 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(main())