from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# ---------- SETUP ----------
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()
wait = WebDriverWait(driver, 25)

driver.get("https://sunbeaminfo.in/")
time.sleep(4)

# ---------- CLICK VIEW MORE ----------
driver.execute_script("window.scrollTo(0, 2000);")
time.sleep(3)

locators = [
    "(//i[@class='fa fa-arrow-circle-o-right'])[1]/parent::a",
    "//a[contains(@href,'pre-cat')]",
    "//h4[contains(text(),'Entrance Preparatory')]/following::a[1]"
]

btn = None
for locator in locators:
    try:
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, locator)))
        driver.execute_script("arguments[0].click();", btn)
        break
    except:
        pass

if not btn:
    raise Exception("VIEW MORE button not found.")

time.sleep(4)

if "pre-cat" not in driver.current_url:
    raise Exception("Not on PRE-CAT page.")

# ---------- SCROLL TO ACCORDION ----------
driver.execute_script("window.scrollTo(0, 700);")
time.sleep(2)

# ---------- CLICK ACCORDIONS ----------
def open_section(href):
    xpath = f"//a[@href='#{href}']/i"
    el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
    driver.execute_script("arguments[0].click();", el)
    time.sleep(2)

# 🚩 SECTION 1: COURSE CONTENTS
open_section("collapse1")
contents = [li.text for li in driver.find_elements(By.CSS_SELECTOR, "#collapse1 li")]

# 🚩 SECTION 2: ELIGIBILITY
open_section("collapse2")
eligibility = driver.find_element(By.ID, "collapse2").text.strip()

# 🚩 SECTION 3: PRE-CAT BATCH SCHEDULE
open_section("collapseThree")
rows = driver.find_elements(By.CSS_SELECTOR, "#collapseThree tbody tr")
batch_schedule = [ [c.text for c in r.find_elements(By.TAG_NAME, "td")] for r in rows ]

# ---------- SAVE TO TXT ----------
with open("precat_data.txt", "w", encoding="utf-8") as file:
    file.write("===== PRE-CAT COURSE CONTENTS =====\n")
    for item in contents:
        file.write(f"- {item}\n")

    file.write("\n===== ELIGIBILITY CRITERIA =====\n")
    file.write(eligibility + "\n")

    file.write("\n===== PRE-CAT BATCH SCHEDULE =====\n")
    for row in batch_schedule:
        file.write(" | ".join(row) + "\n")

print("📁 Data saved to precat_data.txt")

# ---------- DONE ----------
driver.quit()
