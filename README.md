# Regional Commercial Banking Dashboard

## Overview
This project is a data-driven dashboard for analyzing the financial health of U.S. regional commercial banks using publicly available regulatory data. The goal is to build a structured and repeatable framework for evaluating banks across profitability, efficiency, and risk management.

The system processes FDIC call report data and transforms it into comparable metrics across institutions and over time, enabling both time series and cross-sectional analysis.

---

## Key Features

- **Data Pipeline:** Ingests and processes FDIC call report data
- **Data Standardization:** Handles inconsistencies in reporting across banks and time periods
- **Metric Construction:** Computes key financial indicators including:
  - Charge-off ratios
  - Nonperforming loan (NPL) ratios
  - Capital adequacy measures
- **Scoring Framework:** Aggregates metrics into a weighted scoring system to evaluate banks on a balanced basis
- **Interactive Dashboard:** Streamlit-based interface for visualizing trends and comparing institutions

---

## Tech Stack

- Python
  - pandas (data processing)
  - matplotlib (visualization)
  - streamlit (dashboard interface)

---

## Project Structure

/data # Raw and processed FDIC datasets
/src # Data processing and metric construction logic
/app # Streamlit dashboard application
README.md
requirements.txt


---

## Methodology

The project constructs a consistent analytical framework for comparing banks by:

1. Cleaning and aligning regulatory data across reporting periods
2. Defining stable financial metrics despite variations in reporting structures
3. Aggregating metrics into a weighted scoring system that balances:
   - Profitability
   - Efficiency
   - Risk management

Special attention is given to handling missing or lagged data to preserve comparability and avoid distortions in analysis.

---

## Current Status

This is an active project. The core data pipeline and scoring framework are implemented, and the dashboard supports exploratory analysis across a set of regional banks. Future extensions may include additional data sources, expanded coverage, and integration of forecasting or relative value analysis.

---

## Usage

1. Install dependencies: pip install -r requirements.txt

2. Run the dashboard: streamlit run app/streamlit_app.py

---

## Notes

This project is intended for research and analytical purposes. It is designed to explore how structured data pipelines and consistent metric definitions can improve the comparability of financial institutions using publicly available data.