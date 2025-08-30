# 🚗 GCS: GETCHA Scraper  

> **Automated Web Scraper for Imported Car Discounts**  
> A Python-based scraper that collects daily discount data from the **GETCHA Mobile Website** and exports it into Excel for analysis.  
> This project replaces manual data gathering and provides **real-time competitive insights** for business and marketing teams.  
> Previous human scraping was done twice a month, at the beginning and end of each month. Each time it took **at least half a
day, often a full day,** making it quite a draining job with a possibility of human error.
> Daily monitoring of competitor's (MB) discount rates to track competitor's price strategy/competitiveness.
---

# 📄 Overview 
<img width="1034" height="522" alt="image" src="https://github.com/user-attachments/assets/77b98312-84bc-4c06-a5d9-a7793da6c310" />

---
Carried out under the theme of “Enhancing Business Efficiency,” delivering automation to replace time-consuming manual processes.
<img width="1033" height="553" alt="image" src="https://github.com/user-attachments/assets/dce4a7e7-deb5-4f1c-92b1-7701bed60849" />
<img width="1001" height="553" alt="image" src="https://github.com/user-attachments/assets/2e6f4441-1e8b-42bb-a096-85efa32758d9" />

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

## ⚒️ Installation

1. Clone the repository:
   ```
   git clone https://atc-github.azure.cloud.bmw/nsckrit/nsckr-autoscrap.git
   ```

2. Start a program: [`run-autoscrap.bat`] (located in the project directory).

---

## ⚙️ Usage

1. Ensure you have the necessary web drivers installed for Selenium (e.g., ChromeDriver for Google Chrome).
2. Update the `urls.json` file in src directory with the URLs you want to scrape.

---

## 📦 Example Output

car_data_20250625.xlsx
scraping.log


---

## 🚀 Future Improvements
	•	☁️ Migrate to AWS Lambda.
	•	🔧 Integrate with MCP for lifecycle management.

