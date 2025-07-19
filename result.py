import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import sys
import re
from collections import OrderedDict # To maintain insertion order for columns

# For Jupyter/IPython environments, to display DataFrames directly
try:
    from IPython.display import display
except ImportError:
    def display(df):
        print(df.to_string())


def get_fbise_ssc_result(reg_id):
    """
    Fetches the FBISE SSC result for a given registration ID using a GET request.
    This version is specifically tailored to the full HTML structure provided.
    """
    result_url = f"https://portal.fbise.edu.pk/fbise-conduct/result/Result-link-ssc1.php?rollNo={reg_id}&name=&annual=SSC-I"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,application/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://portal.fbise.edu.pk/fbise-conduct/result/Result-link-ssc1.php',
        'Connection': 'keep-alive',
    }

    try:
        response = requests.get(result_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Use OrderedDict to maintain column order for readability in the final CSV
        data = OrderedDict()
        data["Registration ID"] = reg_id
        data["Page Status"] = "Parsing Failed" # Default status
        # Removed "Extracted Registration No" column as requested
        # Removed "ID No" column as requested
        # Removed "Extracted Roll No" column as requested
        data["Group/Trade"] = "N/A"
        data["Student Name"] = "N/A"
        data["Father Name"] = "N/A"
        data["Obtained Marks"] = "N/A" # Renamed from "Total Marks"
        # Removed "Grade" column as requested
        data["Institution"] = "N/A"
        # Subject Marks will be processed separately for flattening later
        data["_Subject_Marks_Raw"] = [] # Temporary key to store raw subject data

        # Check for "Result Not Found" messages first
        page_text_lower = response.text.lower()
        if "result not found" in page_text_lower or \
           "invalid roll number" in page_text_lower or \
           "no record found" in page_text_lower or \
           "sorry, no data found" in page_text_lower:
            print(f"    [INFO] Result not found or invalid for {reg_id}.")
            data["Page Status"] = "Result Not Found"
            return data

        # --- Step 1: Find the main content div ---
        main_content_div = soup.find('div', id='element-to-print', class_='WordSection1')
        if not main_content_div:
            print(f"    [WARN] Main content div (id='element-to-print') not found for {reg_id}.")
            return data

        # --- Step 2: (Skipped Extracted Registration Number parsing as column is removed) ---
        # reg_p_tag = main_content_div.find('p', class_='MsoBodyText', align='right')
        # if reg_p_tag:
        #     reg_match = re.search(r'REG:\s*(\d+)', reg_p_tag.get_text())
        #     if reg_match:
        #         # No longer storing this in data
        #         pass


        # --- Step 3: Find the <p> tag containing Personal and Institution Details Tables ---
        personal_inst_p_tag = None
        for p_tag in main_content_div.find_all('p', class_='MsoBodyText'):
            if 'margin-top:-1in' in p_tag.get('style', '') and p_tag.find('table'):
                personal_inst_p_tag = p_tag
                break

        if personal_inst_p_tag:
            # --- Personal Details Table (First table inside personal_inst_p_tag) ---
            personal_details_table = personal_inst_p_tag.find('table', style=lambda s: s and 'width: 458px' in s)
            if personal_details_table:
                rows = personal_details_table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if cells:
                        header_text = cells[0].text.strip()
                        value_cell_text = cells[1].text.strip() if len(cells) > 1 else ""

                        # "ID NO:" and "Roll No:" are removed as requested.

                        if "Group/Trade:" in header_text:
                            data["Group/Trade"] = value_cell_text
                        elif "Student Name:" in header_text:
                            data["Student Name"] = value_cell_text
                        elif "Father Name:" in header_text:
                            data["Father Name"] = value_cell_text
                        elif "Marks Obt:" in header_text:
                            marks_text = value_cell_text.upper().strip() # Convert to upper for robust 'COMP' check
                            
                            # Check for "COMP" (compartment)
                            if "COMP" in marks_text or "COMPT" in marks_text: # Check for common variations
                                data["Obtained Marks"] = "COMP"
                            else:
                                # Try to extract numeric marks
                                marks_match = re.search(r'(\d+)\s*MARKS', marks_text, re.IGNORECASE)
                                if marks_match:
                                    data["Obtained Marks"] = marks_match.group(1).strip()
                                else:
                                    # If no numeric marks or COMP/COMPT found, set N/A
                                    data["Obtained Marks"] = "N/A"
            else:
                print(f"    [WARN] Personal details table not found for {reg_id}.")

            # --- Institution Details Table (Second table inside personal_inst_p_tag) ---
            institution_table = personal_inst_p_tag.find('table', width="700px")
            if institution_table:
                inst_row = institution_table.find('tr')
                if inst_row:
                    inst_cells = inst_row.find_all('td')
                    if len(inst_cells) > 1 and "INSTITUTION:" in inst_cells[0].text:
                        data["Institution"] = inst_cells[1].text.strip()
            else:
                print(f"    [WARN] Institution table not found for {reg_id}.")
        else:
            print(f"    [WARN] Specific <p> tag containing personal/institution tables not found for {reg_id}.")


        # --- Step 4: Extract Subject-wise Marks Table ---
        subject_marks_div = None
        if personal_inst_p_tag:
            for sibling in personal_inst_p_tag.find_next_siblings('div'):
                if sibling.find('table', class_='MsoNormalTable'):
                    subject_marks_div = sibling
                    break
        
        if not subject_marks_div: # Fallback if direct sibling search fails
            subject_marks_div = main_content_div.find('div', style=lambda s: s and 'border: solid 0px;height: 59vh;' in s)
            
        if subject_marks_div:
            subject_table = subject_marks_div.find('table', class_='MsoNormalTable')
            if subject_table:
                rows = subject_table.find_all('tr')
                if len(rows) > 1: # Skip header row
                    for row in rows[1:]:
                        cols = row.find_all('td')
                        # Check for at least 3 columns for S.#, Subject, Theory Marks (index 2)
                        # We are explicitly ignoring Practical Marks (index 3) now.
                        if len(cols) >= 3:
                            theory_raw_text = cols[2].text.strip()
                            
                            # Determine theory marks: "COMP", numeric, or "N/A"
                            theory_marks = "N/A" # Default
                            if "COMP" in theory_raw_text.upper() or "COMPT" in theory_raw_text.upper():
                                theory_marks = "COMP"
                            elif re.match(r'^\d+$', theory_raw_text):
                                theory_marks = theory_raw_text # It's a number

                            subject_entry = {
                                "S.#": cols[0].text.strip(),
                                "Subject": cols[1].text.strip(),
                                "Theory Marks": theory_marks,
                                # Practical Marks are no longer stored in the raw data list
                            }
                            data["_Subject_Marks_Raw"].append(subject_entry)
                else:
                    print(f"    [WARN] Subject marks table found, but no data rows for {reg_id}.")
            else:
                print(f"    [WARN] Subject marks table (MsoNormalTable) not found for {reg_id}.")
        else:
            print(f"    [WARN] Subject marks main div not found for {reg_id}.")


        # Determine overall status after parsing attempts
        # "Success" if student name and obtained marks (numeric or "COMP") are found
        # Now, "Partial Success" is more about structural issues preventing core data extraction
        if data["Student Name"] != "N/A" and data["Obtained Marks"] != "N/A":
            data["Page Status"] = "Success"
        elif data["Registration ID"] != "N/A": # If we at least have the Registration ID that was processed
             data["Page Status"] = "Partial Success (Key Data Missing)"
        else: # If even the initial Registration ID isn't set (shouldn't happen with current logic)
            data["Page Status"] = "Parsing Failed (No Core Data)"


        return data

    except requests.exceptions.HTTPError as e:
        print(f"    [ERROR] HTTP error for {reg_id}: {e} - Status Code: {e.response.status_code}")
        data["Page Status"] = f"HTTP Error {e.response.status_code}"
        return data
    except requests.exceptions.ConnectionError as e:
        print(f"    [ERROR] Connection error for {reg_id}: {e} - Check internet connection or URL.")
        data["Page Status"] = "Connection Error"
        return data
    except requests.exceptions.Timeout:
        print(f"    [ERROR] Timeout for {reg_id}: Server took too long to respond.")
        data["Page Status"] = "Timeout"
        return data
    except Exception as e:
        print(f"    [ERROR] An unexpected error occurred for {reg_id}: {e}", file=sys.stderr)
        data["Page Status"] = f"Error: {str(e)[:50]}"
        return data


def run_fbise_ssc_automation_mvp(start_reg_id, end_reg_id, output_csv="fbise_ssc_results_mvp.csv"):
    """
    Runs the MVP automation to fetch FBISE SSC results for a range of consecutive IDs.
    """
    all_results = []
    # Keep track of all unique subject names encountered to ensure consistent columns
    all_subject_names = OrderedDict() # Use OrderedDict to maintain consistent column order

    print(f"--- FBISE SSC Result Automation MVP ---")
    print(f"Attempting to fetch results for Registration IDs from {start_reg_id} to {end_reg_id}.")
    print(f"Output will be saved to: {output_csv}")
    print(f"**Parsing Logic Update:** 'Obtained Marks' column added, 'COMP' handled. 'Grade', 'ID No', 'Extracted Roll No', 'Extracted Registration No', and all 'Practical Marks' columns removed.")
    print("-" * 40)

    for i, reg_id in enumerate(range(start_reg_id, end_reg_id + 1)):
        print(f"Processing Reg ID: {reg_id} ({i+1}/{end_reg_id - start_reg_id + 1})")
        result = get_fbise_ssc_result(reg_id)
        if result:
            processed_result = OrderedDict(result) # Create a modifiable copy and ensure order

            # Process subject marks for flattening
            raw_subject_marks = processed_result.pop("_Subject_Marks_Raw", [])
            for subject_entry in raw_subject_marks:
                subject_name = subject_entry["Subject"]
                
                # Use full subject name for column headers for clarity
                subject_name_cleaned = subject_name 

                theory_col = f"{subject_name_cleaned} Theory Marks"
                # Practical Marks column creation is explicitly removed here

                processed_result[theory_col] = subject_entry["Theory Marks"]
                
                # Add to our master list of all subject columns encountered
                all_subject_names[theory_col] = None

            all_results.append(processed_result)

        # Introduce a delay to be polite and avoid rate-limiting
        time.sleep(2)

    if all_results:
        # Before creating the DataFrame, ensure all dictionaries have all subject columns
        # with "N/A" if a specific subject was not found for that student.
        final_columns_order = list(all_results[0].keys()) # Start with common columns
        
        # Add all unique subject columns to the end in the order they were first encountered
        for col in all_subject_names.keys():
            if col not in final_columns_order: # Avoid duplicating initial columns
                final_columns_order.append(col)

        # Fill in missing subject columns for each student
        for student_data in all_results:
            for col in all_subject_names.keys():
                if col not in student_data:
                    student_data[col] = "N/A" # Fill with N/A if subject not present for this student
            
            # Ensure the order of columns for consistency
            ordered_student_data = OrderedDict()
            for col_name in final_columns_order:
                if col_name in student_data:
                    ordered_student_data[col_name] = student_data[col_name]

            # Replace the original student_data with the ordered one
            all_results[all_results.index(student_data)] = ordered_student_data


        df = pd.DataFrame(all_results)
        df.to_csv(output_csv, index=False)
        print(f"\n--- Automation Complete ---")
        print(f"Results compiled successfully to {output_csv}")
        print(f"Total results attempted: {end_reg_id - start_reg_id + 1}")
        print(f"Total results fetched (successful or with status): {len(all_results)}")
        print(f"Summary of statuses:\n{df['Page Status'].value_counts()}")

        # Display results that were parsed successfully
        successful_df = df[df['Page Status'] == 'Success']
        if not successful_df.empty:
            print("\n--- Sample of Successfully Parsed Results (Main Data) ---")
            display(successful_df.head())
        else:
            print("\n--- No Main Results Successfully Parsed ---")

    else:
        print("\n--- Automation Complete ---")
        print("No results were successfully processed.")

if __name__ == "__main__":
    # --- CONFIGURE YOUR REGISTRATION ID RANGE HERE ---
    start_registration_id = 9024110
    end_registration_id = 9024120 # Adjust this range as needed for testing

    run_fbise_ssc_automation_mvp(start_registration_id, end_registration_id)

    print("\n--- Next Steps ---")
    print("1. **Verify the output CSV:** Open `fbise_ssc_results_mvp.csv` to ensure the data is parsed correctly and subject columns are present.")
    print("2. If any data points are still 'N/A' or incorrect for known good IDs, re-inspect the live HTML to find precise selectors or patterns.")
    print("3. Remember to respect the website's `robots.txt` and terms of service. Excessive or rapid requests can lead to IP blocking.")