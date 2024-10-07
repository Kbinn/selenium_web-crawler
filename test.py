from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
from time import sleep


driver = webdriver.Chrome()


driver.get("file:///D:/chromedriver/report.html")


record_id_script = "return current_record_id;"
current_record_id = driver.execute_script(record_id_script)
print("current_record_id:", current_record_id)

new_page_url = f"file:///D:/chromedriver/{current_record_id}.html"


driver.get(new_page_url)


wait = WebDriverWait(driver, 20)
yellow_options = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//label[contains(@class, 'selectedItem')]")))


with open('selected_items.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Question', 'Selected Answer']) 


    for option in yellow_options:
        question = option.find_element(By.XPATH, './preceding-sibling::h4').text  
        selected_answer = option.text
        writer.writerow([question, selected_answer])  

sleep(100)


driver.quit()
