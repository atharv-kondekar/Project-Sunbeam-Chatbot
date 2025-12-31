from selenium import webdriver 
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

URL = "https://www.sunbeaminfo.in/modular-courses.php?mdid=57"

options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 20)
driver.get(URL)

# ---------------- WAIT FOR PAGE ----------------
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
time.sleep(3)

# ---------------- OPEN OUTPUT FILE ----------------
output_file = open("modular_course_mdid_57.txt", "w", encoding="utf-8")

def write(text=""):
    output_file.write(text + "\n")

# ---------------- COURSE INFO ----------------
write("========== COURSE DETAILS ==========\n")

title = driver.find_element(By.CSS_SELECTOR, "h3.inner_page_head").text
write(f"Course Title: {title}\n")

info = driver.find_elements(By.CSS_SELECTOR, ".course_info p")
for p in info:
    if p.text.strip():
        write(p.text.strip())

# ---------------- ACCORDION SCRAPER ----------------
def expand_and_scrape_by_index(index, label):
    write(f"\n========== {label.upper()} ==========\n")

    accordions = driver.find_elements(
        By.CSS_SELECTOR,
        ".panel-heading a[data-toggle='collapse']"
    )

    target = accordions[index]

    driver.execute_script("arguments[0].scrollIntoView(true);", target)
    time.sleep(1)

    driver.execute_script("arguments[0].click();", target)

    panel_id = target.get_attribute("href").split("#")[-1]

    panel = wait.until(
        EC.visibility_of_element_located((By.ID, panel_id))
    )

    time.sleep(1)

    items = panel.find_elements(By.TAG_NAME, "li")
    if items:
        for li in items:
            write("- " + li.text.strip())
    else:
        text = panel.text.strip()
        if text:
            write(text)

# ---------------- SCRAPE ALL SECTIONS ----------------
expand_and_scrape_by_index(0, "Target Audience")
expand_and_scrape_by_index(1, "Course Contents")
expand_and_scrape_by_index(2, "Batch Schedule")

write("\n✅ Modular Course Data Scraped Successfully")

# ---------------- CLEANUP ----------------
output_file.close()
time.sleep(5)
driver.quit()
