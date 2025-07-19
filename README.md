# FBISE SSC Result Automation MVP

## Project Description
This project automates the process of fetching and compiling Federal Board of Intermediate and Secondary Education (FBISE) SSC (Secondary School Certificate) results for a range of registration IDs. It is designed to help students, parents, and educational institutions quickly retrieve and analyze results in bulk, saving time and effort compared to manual lookup.

The script scrapes the official FBISE results portal, parses the relevant data (including student details, obtained marks, and subject-wise marks), and exports the results to a CSV file for further analysis or record-keeping. The code is robust, handles various error scenarios, and is easily customizable for different registration ID ranges.

---

## Features
- Fetches results for a user-defined range of registration IDs.
- Parses student name, father name, group/trade, institution, obtained marks, and subject-wise theory marks.
- Handles special cases such as "COMP" (compartment) and missing data.
- Outputs results to a CSV file with consistent columns for easy analysis.
- Provides detailed status messages for each registration ID (success, not found, errors, etc.).
- Polite scraping: includes delays to avoid overloading the server.

---

## Requirements
- Python 3.7+
- Required packages:
  - requests
  - beautifulsoup4
  - pandas

You can install the dependencies using pip:

```bash
pip install requests beautifulsoup4 pandas
```

---

## Usage

1. **Clone the repository or copy the script to your local machine.**

2. **Edit the registration ID range:**
   
   Open `result.py` and modify the following lines at the bottom of the script to set your desired range:
   
   ```python
   start_registration_id = 9024110  # Change to your starting ID
   end_registration_id = 9024120    # Change to your ending ID
   ```

3. **Run the script:**

   Open a terminal in the project directory and run:
   
   ```bash
   python result.py
   ```

4. **Check the output:**
   
   The results will be saved in a CSV file named `fbise_ssc_results_mvp.csv` in the same directory. Open this file with Excel, Google Sheets, or any CSV viewer to review the results.

5. **Review the console output:**
   
   The script prints status messages for each registration ID processed, including errors and a summary at the end.

---

## Notes
- The script is for educational and personal use. Please respect the FBISE website's terms of service and avoid excessive or rapid requests.
- If you encounter issues with missing or incorrect data, inspect the live HTML structure of the results page and adjust the parsing logic as needed.
- The script does not store or process practical marks or grades, focusing only on theory marks and main details.

---

## Example Output
A sample of the output CSV columns:

| Registration ID | Page Status | Group/Trade | Student Name | Father Name | Obtained Marks | Institution | [Subject 1 Theory Marks] | [Subject 2 Theory Marks] | ... |
|-----------------|------------|-------------|--------------|-------------|---------------|-------------|-------------------------|-------------------------|-----|

---

## License
This project is open-source and free to use for non-commercial purposes. Please credit the author if you use or modify the code.

---

## Author
- Sabbas Ahmad
- Mail sabbbas.a30@gmail.com
