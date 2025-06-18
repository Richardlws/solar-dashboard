from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd

# 设置浏览器无头模式（可选）
chrome_options = Options()
# chrome_options.add_argument("--headless")  # 如需可视化运行，请注释掉这一行

driver = webdriver.Chrome(options=chrome_options)
driver.get("https://www.lagou.com/")

time.sleep(3)

# 搜索“后端 实习”
keyword = "后端 实习"
city = "北京"
driver.get(f"https://www.lagou.com/jobs/list_{keyword}?city={city}")
time.sleep(5)

job_list = []

# 多页爬取
for page in range(1, 3):  # 示例：爬前2页
    print(f"📄 第 {page} 页")
    time.sleep(3)
    job_cards = driver.find_elements(By.CLASS_NAME, 'list__item__wrap')

    for card in job_cards:
        try:
            title = card.find_element(By.CLASS_NAME, "p-top__1").text
            company = card.find_element(By.CLASS_NAME, "company__2A8S").text
            salary = card.find_element(By.CLASS_NAME, "p-bom__1").text
            detail = card.find_element(By.CLASS_NAME, "p-bom__2").text
            job_list.append({
                "岗位": title,
                "公司": company,
                "薪资": salary,
                "详情": detail
            })
        except:
            continue

    try:
        next_btn = driver.find_element(By.CLASS_NAME, 'pager_next')
        if "disabled" in next_btn.get_attribute("class"):
            break
        next_btn.click()
    except:
        break

driver.quit()

# 保存数据
df = pd.DataFrame(job_list)
df.to_excel("lagou_jobs.xlsx", index=False)
print("✅ 已保存职位到 lagou_jobs.xlsx，共爬取", len(df), "条")
