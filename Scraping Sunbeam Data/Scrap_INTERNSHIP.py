from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

URL = "https://www.sunbeaminfo.in/internship"

options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 25)
driver.get(URL)

time.sleep(4)  # allow animations to complete

# -------------------------------------------------
# OPEN OUTPUT FILE
# -------------------------------------------------
output_file = open("internship_data.txt", "w", encoding="utf-8")

def write(text=""):
    output_file.write(text + "\n")

# -------------------------------------------------
# PAGE TITLE
# -------------------------------------------------
write("========== INTERNSHIP PAGE ==========\n")

title = driver.find_element(By.CSS_SELECTOR, "h3.inner_page_head").text
write(f"Page Title: {title}\n")

# -------------------------------------------------
# INTRO DESCRIPTION
# -------------------------------------------------
intro = driver.find_elements(By.CSS_SELECTOR, ".about_page p")
for p in intro:
    if p.text.strip():
        write(p.text.strip())

# -------------------------------------------------
# ACCORDION SCRAPER BY INDEX
# -------------------------------------------------
def scrape_accordion(index, section_name):
    write(f"\n========== {section_name.upper()} ==========\n")

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
        write(panel.text.strip())

# -------------------------------------------------
# SCRAPE ALL REQUIRED SECTIONS
# -------------------------------------------------
scrape_accordion(0, "Student Industrial Training & Internship")
scrape_accordion(1, "Training And Industrial Program Features")
scrape_accordion(2, "Placements")
scrape_accordion(3, "Benefits Of Program")
scrape_accordion(4, "Our Associates")
scrape_accordion(5, "Available Internship Programs")

# -------------------------------------------------
# INTERNSHIP BATCH SCHEDULE TABLE
# -------------------------------------------------
write("\n========== INTERNSHIP BATCHES SCHEDULE ==========\n")

table = wait.until(
    EC.presence_of_element_located(
        (By.CSS_SELECTOR, ".table-responsive table")
    )
)

headers = table.find_elements(By.TAG_NAME, "th")
write(" | ".join(h.text for h in headers))

rows = table.find_elements(By.TAG_NAME, "tr")[1:]

for row in rows:
    cols = row.find_elements(By.TAG_NAME, "td")
    row_data = [c.text.strip() for c in cols]
    write(" | ".join(row_data))

write("\n✅ Internship Data Scraped Successfully")

# -------------------------------------------------
# CLEANUP
# -------------------------------------------------
output_file.close()
time.sleep(5)
driver.quit()
