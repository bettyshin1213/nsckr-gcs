import pandas as pd
import os
import logging
from datetime import datetime
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def load_data_files(date=None):
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    data_dir = Path("data")
    
    car_data_path = data_dir / f"car_data_{date}.xlsx"
    car_data_web_path = data_dir / f"etc/car_data_web_{date}.xlsx"
    
    if not car_data_path.exists():
        logging.error(f"파일이 존재하지 않습니다: {car_data_path}")
        return None, None, None
    
    if not car_data_web_path.exists():
        logging.error(f"파일이 존재하지 않습니다: {car_data_web_path}")
        return None, None, None
    
    try:
        car_data_df = pd.read_excel(car_data_path)
        car_data_web_df = pd.read_excel(car_data_web_path)
        
        logging.info(f"car_data_{date}.xlsx: {len(car_data_df)}행 로드됨")
        logging.info(f"etc/car_data_web_{date}.xlsx: {len(car_data_web_df)}행 로드됨")
        
        return car_data_df, car_data_web_df, car_data_path
    
    except Exception as e:
        logging.error(f"데이터 로드 중 오류 발생: {e}")
        return None, None, None

def preprocess_data(car_data_df, car_data_web_df):
    if car_data_df is None or car_data_web_df is None:
        return None, None
    
    try:
        if 'MY' in car_data_df.columns:
            car_data_df = car_data_df[['Brand', 'Series', 'MY', 'Model (adjusted)', 'MSRP', 'Cash_off', 'Finance_off']]
        else:
            car_data_df = car_data_df[['Brand', 'Series', 'Model (adjusted)', 'MSRP', 'Cash_off', 'Finance_off']]
            car_data_df['MY'] = '25'
        
        if 'MY' in car_data_web_df.columns:
            car_data_web_df = car_data_web_df[['Brand', 'Series', 'MY', 'Model', 'MSRP', 'Off']]
        else:
            car_data_web_df = car_data_web_df[['Brand', 'Series', 'Model', 'MSRP', 'Off']]
            car_data_web_df['MY'] = '25'
        
        car_data_df = car_data_df.rename(columns={'Model (adjusted)': 'Model'})
        
        car_data_df['MSRP'] = car_data_df['MSRP'].astype(str).str.replace(',', '').replace('', '0').fillna('0')
        car_data_web_df['MSRP'] = car_data_web_df['MSRP'].astype(str).str.replace(',', '').replace('', '0').fillna('0')
        
        car_data_df['Cash_off'] = car_data_df['Cash_off'].astype(str).str.replace(',', '').replace('', '0').fillna('0')
        car_data_df['Finance_off'] = car_data_df['Finance_off'].astype(str).str.replace(',', '').replace('', '0').fillna('0')
        car_data_web_df['Off'] = car_data_web_df['Off'].astype(str).str.replace(',', '').replace('만원', '').replace('', '0').fillna('0')
        
        car_data_df['MY'] = car_data_df['MY'].astype(str)
        car_data_web_df['MY'] = car_data_web_df['MY'].astype(str)
        
        return car_data_df, car_data_web_df
    
    except Exception as e:
        logging.error(f"데이터 전처리 중 오류 발생: {e}")
        return None, None

def ensure_directories():
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/etc", exist_ok=True)

def compare_data(car_data_df, car_data_web_df, car_data_path, date=None):
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    if car_data_df is None or car_data_web_df is None:
        return
    
    ensure_directories()
    
    discrepancies = []
    
    # car_data_web에서 할인(Off)이 있는 모델만 필터링
    web_models_with_off = car_data_web_df[car_data_web_df['Off'] != '0']
    
    logging.info(f"할인 제공 모델 수: {len(web_models_with_off)}")
    
    missing_models = []
    
    for _, web_row in web_models_with_off.iterrows():
        # car_data에서 일치하는 모델 찾기 (Brand, Series, MY, Model 모두 일치하는 경우)
        matching_models = car_data_df[
            (car_data_df['Brand'] == web_row['Brand']) & 
            (car_data_df['Series'] == web_row['Series']) & 
            (car_data_df['MY'] == web_row['MY']) &
            (car_data_df['Model'] == web_row['Model'])
        ]

        if len(matching_models) == 0:
            # Web_Off가 유효한 값일 때만 문제로 간주
            if web_row['Off'] not in ['nan', 'Not Found', 'N/A', '0']:
                discrepancy = {
                    'Brand': web_row['Brand'],
                    'Series': web_row['Series'],
                    'MY': web_row['MY'],
                    'Model': web_row['Model'],
                    'Web_MSRP': web_row['MSRP'],
                    'Web_Off': web_row['Off'],
                    'App_MSRP': 'Not Found',
                    'App_Cash_off': 'Not Found',
                    'App_Finance_off': 'Not Found',
                    'Issue': 'Model not found in app data'
                }
                discrepancies.append(discrepancy)

                today = datetime.now()
                missing_model = {
                    'Year': today.year,
                    'Month': today.month,
                    'Date': today.day,
                    'Brand': web_row['Brand'],
                    'MY': web_row['MY'],
                    'Series': web_row['Series'],
                    'Fuel Type': '',
                    'Model (adjusted)': web_row['Model'],
                    'MSRP': web_row['MSRP'],
                    'Cash_off': '',
                    'Finance_off': '',
                    'Validated': 'X'
                }
                missing_models.append(missing_model)
            continue
        
        # 일치하는 모델이 있는 경우 비교
        for _, app_row in matching_models.iterrows():
            issues = []

            web_msrp = web_row['MSRP']
            app_msrp = app_row['MSRP']
            
            # 유효한 값인지 체크 (nan, not found 등이 아닌지)
            if (web_msrp not in ['nan', 'Not Found', 'N/A'] and 
                app_msrp not in ['nan', 'Not Found', 'N/A'] and 
                web_msrp != app_msrp):
                issues.append(f"MSRP mismatch: Web={web_msrp}, App={app_msrp}")
            
            web_off = web_row['Off']
            app_cash_off = app_row['Cash_off']
            app_finance_off = app_row['Finance_off']
            # nan, not found 등의 값은 비교에서 제외
            valid_comparison = (
                web_off not in ['nan', 'Not Found', 'N/A', '0'] and
                app_cash_off not in ['nan', 'Not Found', 'N/A', '0'] and
                app_finance_off not in ['nan', 'Not Found', 'N/A', '0']
            )
            
            # 유효한 값이고 웹 할인이 앱 현금 할인이나 금융 할인 중 하나와 일치하지 않는 경우만 이슈로 처리
            if valid_comparison and web_off != app_cash_off and web_off != app_finance_off:
                issues.append(f"Discount mismatch: Web={web_off}, App Cash={app_cash_off}, App Finance={app_finance_off}")
            
            # 특별 케이스 처리: 모든 값이 'nan', 'Not Found' 등인 경우는 문제 없음으로 처리
            if (web_row['Off'] in ['nan', 'Not Found', 'N/A'] and 
                app_row['MSRP'] in ['nan', 'Not Found', 'N/A'] and 
                app_row['Cash_off'] in ['nan', 'Not Found', 'N/A'] and 
                app_row['Finance_off'] in ['nan', 'Not Found', 'N/A']):
                continue
            
            if issues:                
                discrepancies.append({
                    'Brand': web_row['Brand'],
                    'Series': web_row['Series'],
                    'MY': web_row['MY'],
                    'Model': web_row['Model'],
                    'Web_MSRP': web_row['MSRP'],
                    'Web_Off': web_row['Off'],
                    'App_MSRP': app_row['MSRP'],
                    'App_Cash_off': app_row['Cash_off'],
                    'App_Finance_off': app_row['Finance_off'],
                    'Issue': '; '.join(issues)
                })
    
    if discrepancies:
        discrepancies_df = pd.DataFrame(discrepancies)
        output_file = f"data/etc/discrepancies_{date}.xlsx"
        
        # 이미 파일이 존재하더라도 새 데이터로 덮어쓰기 (기존 데이터는 버림)
        with pd.ExcelWriter(output_file, engine="openpyxl", mode="w") as writer:
            discrepancies_df.to_excel(writer, index=False)
        
        logging.info(f"불일치 항목 {len(discrepancies)}개 발견, 결과 저장됨: {output_file} (기존 데이터 덮어씀)")
    else:
        logging.info("모든 할인 모델이 일치합니다.")
    
    if missing_models:
        try:
            original_df = pd.read_excel(car_data_path)
            
            if 'Validated' not in original_df.columns:
                original_df['Validated'] = 'O'
            
            missing_df = pd.DataFrame(missing_models)
            
            updated_df = pd.concat([original_df, missing_df], ignore_index=True)
            
            with pd.ExcelWriter(car_data_path, engine="openpyxl", mode="w") as writer:
                updated_df.to_excel(writer, index=False)
            
            logging.info(f"앱에 없는 모델 {len(missing_models)}개를 {car_data_path}에 추가했습니다.")
        except Exception as e:
            logging.error(f"앱 데이터 업데이트 중 오류 발생: {e}")

def main(date=None):
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    car_data_df, car_data_web_df, car_data_path = load_data_files(date)
    if car_data_df is None or car_data_web_df is None:
        return
    
    car_data_df, car_data_web_df = preprocess_data(car_data_df, car_data_web_df)
    if car_data_df is None or car_data_web_df is None:
        return
    
    compare_data(car_data_df, car_data_web_df, car_data_path, date)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='자동차 할인 데이터 비교 도구')
    parser.add_argument('--date', type=str, help='비교할 데이터 날짜 (YYYYMMDD 형식)')
    
    args = parser.parse_args()
    
    main(args.date)