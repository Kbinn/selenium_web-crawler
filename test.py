from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv

driver = webdriver.Chrome()
driver.get("2021-04-07_2009_28_28.005_1284114214.html")



record_id_script = "return current_record_id;"
current_record_id = driver.execute_script(record_id_script)
current_record_id = current_record_id.replace(' ', '_20').replace(':', '_').replace(';', '_')
print("current_record_id:", current_record_id)

new_page_url = f"file:///C:/Users/user/Downloads/test/{current_record_id}.html"
driver.get(new_page_url)

wait = WebDriverWait(driver, 20)
questions = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h4")))

output_path = f"C:/Users/user/Downloads/test/output/{current_record_id}.csv"
with open(output_path, "w", newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    for question in questions:
        question_text = question.text
        try:
            selected_answer = question.find_element(By.XPATH, "./following-sibling::div[1]").find_element(By.CSS_SELECTOR, ".selectedItem").text
           
            combined_text = f"{question_text}\n{selected_answer}"
            writer.writerow([combined_text])
            print(f'{combined_text}')
            print("-" * 20)
        except Exception as e:
            error_message = f'Error finding selected answer for question "{question_text}": {str(e)}'
            print(error_message)
            
            writer.writerow([f"{question_text}\nNo answer selected"])

driver.quit()
