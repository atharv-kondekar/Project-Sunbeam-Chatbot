from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

#Browser Setup
options = Options()
driver = webdriver.Chrome(options=options)
driver.set_window_size(1280, 900)

#Loading the Websites and initialize the wait stratergy 
driver.get("https://sunbeaminfo.in/")
wait = WebDriverWait(driver, 20)

# navigating to the About us 
about_menu = wait.until(
    EC.visibility_of_element_located((By.XPATH, "//a[contains(text(),'About Us')]"))
)
ActionChains(driver).move_to_element(about_menu).pause(1).perform()


about_us = wait.until(
    EC.element_to_be_clickable((By.XPATH, "//a[@href='about-us']"))
)
ActionChains(driver).move_to_element(about_us).click().perform()


# Extract the Content
content_block = wait.until(
    EC.visibility_of_element_located((By.CSS_SELECTOR, "div.main_info"))
)
text = content_block.text.strip()

#Saved into the file
with open("about_sunbeam.txt", "w", encoding="utf-8") as file:
    file.write(text)

print("Data saved to about_sunbeam.txt")

driver.quit()
