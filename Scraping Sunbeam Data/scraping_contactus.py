from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

URL = "https://www.sunbeaminfo.in/contact-us"

# ---------------- BROWSER SETUP ----------------
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 30)
driver.get(URL)
time.sleep(4)

# ---------------- OUTPUT FILE ----------------
output_file = open("contact_us_full_data.txt", "w", encoding="utf-8")

def write(text=""):
    output_file.write(text + "\n")

# ---------------- PAGE TITLE ----------------
write("========== CONTACT US ==========\n")

title = wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "h3.inner_page_head"))
).text
write(f"Page Title: {title}\n")

# ---------------- OUR CENTRES ----------------
write("========== OUR CENTRES ==========\n")

centres = wait.until(
    EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, ".contact_page_info")
    )
)

for idx, centre in enumerate(centres, start=1):
    write(f"--- Centre {idx} ---")

    # Centre Name
    try:
        name = centre.find_element(By.TAG_NAME, "h4").text.strip()
        write(f"Centre Name: {name}")
    except:
        write("Centre Name: Not Found")

    # Address (paragraphs without links)
    paragraphs = centre.find_elements(By.TAG_NAME, "p")
    for p in paragraphs:
        if not p.find_elements(By.TAG_NAME, "a"):
            text = p.text.strip()
            if text:
                write(f"Address: {text}")

    # 📞 PHONE NUMBERS (FIXED)
    phones = centre.find_elements(
        By.XPATH,
        ".//a[contains(translate(@href,'TEL','tel'),'tel')]"
    )
    for phone in phones:
        write(f"Phone: {phone.text.strip()}")

    # 📧 EMAILS
    emails = centre.find_elements(
        By.XPATH,
        ".//a[contains(translate(@href,'MAILTO','mailto'),'mailto')]"
    )
    for email in emails:
        write(f"Email: {email.text.strip()}")

    # 📍 GOOGLE MAPS
    maps = centre.find_elements(
        By.XPATH,
        ".//a[contains(@href,'google.com/maps')]"
    )
    for m in maps:
        write(f"Location Map: {m.get_attribute('href')}")

    write("")

write("✅ Contact Us Data Scraped Successfully")

# ---------------- CLEANUP ----------------
output_file.close()
time.sleep(5)
driver.quit()
