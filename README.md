# 🚗 GCS: GETCHA Scraper  

> **Automated Web Scraper for Imported Car Discounts**  
> A Python-based scraper that collects daily discount data from the **GETCHA Mobile Website** and exports it into Excel for analysis.  
> This project replaces manual data gathering and provides **real-time competitive insights** for business and marketing teams.  

---

## 🎯 Goals
- Automate the collection of car discount data (BMW, Mini, MB, Audi, VW).  
- Ensure **daily monitoring** of both BMW and competitors’ pricing strategies.  
- Minimize human error and reduce manual workload.  
- Provide structured Excel outputs for further analysis.  

---

## ✨ Key Features
- 🔍 **Brand Series Exploration** – Automatically browses each brand’s series.  
- 💰 **Discount Collection** – MSRP, cash discounts, and finance discounts.  
- ⛽ **Fuel & Year Detection** – Extracts fuel type (P, D, BEV, PHEV) and model year.  
- 🔄 **Duplicate Prevention** – Avoids scraping the same series more than once per day.  
- 📊 **Excel Export** – Saves as `car_data_YYYYMMDD.xlsx`.  
- 📜 **Logging & Error Handling** – Tracks events in `scraping.log`.  

---

## 📂 Data Scope
- **Brands**: BMW, Mini, Mercedes-Benz, Audi, Volkswagen  
- **Fields**:  
  - Scraped Date  
  - Model Name / Series  
  - Model Year  
  - Fuel Type  
  - MSRP (Manufacturer’s Suggested Retail Price)  
  - Cash Discount / Finance Discount  

---

## Installation

1. Clone the repository:
   ```
   git clone https://atc-github.azure.cloud.bmw/nsckrit/nsckr-autoscrap.git
   ```

2. Start a program: [`run-autoscrap.bat`] (located in the project directory).

## Usage

1. Ensure you have the necessary web drivers installed for Selenium (e.g., ChromeDriver for Google Chrome).
2. Update the `urls.json` file in src directory with the URLs you want to scrape.

⸻

📦 Example Output

car_data_20250625.xlsx
scraping.log


⸻


🚀 Future Improvements
	•	☁️ Migrate to AWS Lambda.
	•	🔧 Integrate with MCP for lifecycle management.

⸻

👩‍💻 Authors & Contributors
	•	Owner/Developer: Hyewon Shin (FG-AP-52)
	•	Business User: Gayoung Ryu (C3-KR-V-1)