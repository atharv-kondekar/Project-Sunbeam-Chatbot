import os, time, re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# ======= Setup =======
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()

# The popup killer 
def kill_popups():
    for x in [
        "//*[@id='jivo_close_button']",
        "//a[contains(text(),'OK') or contains(text(),'Accept')]",
        "//*[contains(@class,'wa-widget')]"
    ]:
        try:
            el = driver.find_element(By.XPATH, x)
            driver.execute_script("arguments[0].click();", el)
        except:
            try:
                driver.execute_script("arguments[0].style.display='none';", el)
            except: pass

# clean function
def clean(txt:str):
    if not txt: return ""
    return re.sub(r'\s+', ' ', txt.replace("CLICK TO REGISTER","")).strip()


# ======= Go to home page =======
driver.get("https://sunbeaminfo.in/modular-courses-home")
time.sleep(5)
kill_popups()

# Extracting all courses link
links = list(set([
    e.get_attribute("href").lower()
    for e in driver.find_elements(By.XPATH,"//a[contains(@href,'modular-courses')]")
    if "/modular-courses/" in e.get_attribute("href").lower() and "home" not in e.get_attribute("href").lower()
]))

print(f"\n🎯 Total Courses Found: {len(links)}")

# ======= Create folder =======
os.makedirs("certified courses", exist_ok=True)


# ======= Scrape Course Pages =======
for url in links:
    print(f"\n======================")
    print(f"🔎 {url}")
    driver.get(url)
    time.sleep(3)
    kill_popups()

    # -------- Basic Info --------
    def grab(key):
        try: return clean(driver.find_element(By.XPATH,f"//*[contains(text(),'{key}')]").text)
        except: return ""

    title = grab("Course Name") or grab("Course") or "Unknown"
    duration = grab("Duration")
    schedule = grab("Batch Schedule")
    timings = grab("Timings")
    fees = grab("Fees")
    out = {
        "Course Name": title,
        "Duration":duration,
        "Schedule":schedule,
        "Timings":timings,
        "Fees":fees
    }

    # -------- Accordions Auto-Detect --------
    accordion_headers = driver.find_elements(By.XPATH,"//h4|//h3|//h5")

    for head in accordion_headers:
        try:
            label = clean(head.text).replace(":", "")
            if not label or len(label)<2: continue

            driver.execute_script("arguments[0].scrollIntoView();", head)
            try: head.click()
            except: pass
            time.sleep(1)

            # Get next visible panel
            try:
                panel = head.find_element(By.XPATH,"./following::*[1]")
                txt = clean(panel.text)
                if txt and txt not in out.values():
                    out[label] = txt
                    print(f"✔ {label}")
            except:
                pass

        except Exception as e:
            print("skipped header")

    # -------- Save to file --------
    safe = re.sub(r'[^A-Za-z0-9_\- ]','', title).strip().replace(" ","_")
    file = f"courses/{safe}.txt"

    with open(file,"w",encoding="utf-8") as f:
        f.write("="*40+"\n")
        f.write(f"📌 {title}\n")
        f.write("="*40+"\n\n")

        for k,v in out.items():
            f.write(f"{k}:\n{'-'*20}\n{v}\n\n")

    print(f"💾 Saved → {file}")

driver.quit()
print("\n🎉 DONE — All Courses Scraped!")
