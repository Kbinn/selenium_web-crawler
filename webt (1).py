import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import csv
import os
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from datetime import datetime

def safe_click(driver, by, value, max_retries=3):
    attempts = 0
    while attempts < max_retries:
        try:
            element = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((by, value)))
            element.click()
            return
        except StaleElementReferenceException:
            attempts += 1
            driver.refresh()
            print(f"Trying to recover from StaleElementReferenceException: attempt {attempts}")

def get_element_attribute(driver, by, value, attribute, max_retries=3):
    attempts = 0
    while attempts < max_retries:
        try:
            element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((by, value)))
            return element.get_attribute(attribute)
        except StaleElementReferenceException:
            attempts += 1
            print(f"StaleElementReferenceException encountered: attempt {attempts}")
    raise Exception("Failed to retrieve attribute after several attempts.")

def save_questionnaire_data(driver, current_record_id, pid, quest_type):
    wait = WebDriverWait(driver, 20)
    questions = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h4")))
    current_record_id = current_record_id.replace(' ', '_20').replace(':', '_').replace(';', '_')
    
    directory_path = f"C:/Users/user/Downloads/test/output/quest/{pid}"
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    output_path = f"{directory_path}/{current_record_id}_{quest_type}.csv"
    
    if os.path.exists(output_path):
        print(f"問卷 {output_path} 已存在")
        return False

    existing_data = []
    if os.path.isfile(output_path):
        with open(output_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            existing_data = [row[0] for row in reader]

    with open(output_path, "a", newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for question in questions:
            question_text = question.text
            try:
                selected_answer = question.find_element(By.XPATH, "./following-sibling::div[1]").find_element(By.CSS_SELECTOR, ".selectedItem").text
                combined_text = f"{question_text}\n{selected_answer}"
                if combined_text in existing_data:
                    print(f"問卷 {combined_text} 已存在，跳過儲存。")
                    continue
                writer.writerow([combined_text])
                print(f'{combined_text}')
                print("-" * 20)
            except Exception as e:
                error_message = f'Error finding selected answer for question "{question_text}": {str(e)}'
                print(error_message)
                writer.writerow([f"{question_text}\nNo answer selected"])

    return True

def process_patient(driver, initial_report_url, date_case_id, pid, quest_type, processed_dates):
    start_time = time.time()
    while True:
        if time.time() - start_time > 120:  
            return
        driver.get(initial_report_url)
        try:
            record_id_script = "return current_record_id;"
            current_record_id = driver.execute_script(record_id_script)
            new_page_url = f"={current_record_id}"
            driver.get(new_page_url)
            if "讀取資料失敗" in driver.page_source:
                raise Exception("讀取資料失敗")
            save_questionnaire_data(driver, current_record_id, pid, quest_type)
            driver.get(initial_report_url)
            html = driver.page_source
            date_match = re.search(r'"date":"(\d{4}-\d{2}-\d{2})"', html)
            if date_match:
                next_date = date_match.group(1)
                next_date = datetime.strptime(next_date, "%Y-%m-%d").date()
                if str(next_date) in processed_dates:
                    break
                processed_dates.add(str(next_date))
                url_parts = list(urlparse(initial_report_url))
                query = dict(parse_qs(url_parts[4]))
                query['id'] = f"{next_date};{pid}"
                url_parts[4] = urlencode(query, doseq=True)
                initial_report_url = urlunparse(url_parts)
            else:
                break
        except Exception as e:
            print(f"Error processing patient {date_case_id}: {str(e)}")
            break

def main():
    driver = webdriver.Chrome()
    try:
        # 登入
        driver.get("")
        username_field = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, 'login_id')))
        password_field = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, 'login_pw')))
        username_field.send_keys('')
        password_field.send_keys('')
        submit_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, 'Submit')))
        submit_button.click()
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "mainMenu")))

        manager_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "manager")))
        manager_link.click()
        select = Select(WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.NAME, "scope"))))
        select.select_by_value('0')  # 更換列表狀態 (0:今日,1:等待,2:未編輯)
        safe_click(driver, By.NAME, "refreshButton")

        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//td[@onclick]")))

        processed_patients = set()
        start_time = time.time()

        while True:
            if time.time() - start_time > 120:  # 檢查是否超過兩分鐘
                print("城市停留在同一頁面超過兩分鐘，自動退出")
                break

            elements = driver.find_elements(By.XPATH, "//td[@onclick]")
            if not elements:
                print("DONE")
                break

            for element in elements:
                try:
                    onclick_attr = element.get_attribute("onclick")
                    if "viewReport" in onclick_attr:
                        args = onclick_attr.split('(')[1].split(')')[0].replace("'", "").split(',')
                        date_case_id = args[0].strip()
                        pid = args[1].strip()
                        quest_type = args[2].strip()
                        date, patient_id = date_case_id.split(";")
                        if patient_id not in processed_patients:
                            processed_patients.add(patient_id)
                            processed_dates = set()
                            initial_report_url = f"={pid}&quest={quest_type}&id={date_case_id}"
                            process_patient(driver, initial_report_url, date_case_id, pid, quest_type, processed_dates)
                            
                            driver.get("")
                            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//td[@onclick]")))
                            start_time = time.time()  
                            break  
                except Exception as e:
                    print(f"Error processing patient {date_case_id}: {str(e)}")
                    driver.get("p")
                    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//td[@onclick]")))
                    start_time = time.time()  
                    break  
        print("已經完成全部問卷")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
