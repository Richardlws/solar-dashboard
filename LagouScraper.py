from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import pandas as pd

# 初始化浏览器
driver = webdriver.Chrome()
driver.get("https://www.lagou.com/")

# 搜索关键词
keyword = "后端 实习"
city = "北京"

# 模拟搜索
driver.get(f"https://www.lagou.com/jobs/list_{keyword}?city={city}")
time.sleep(5)

jobs = []

for i in range(1, 4):  # 爬3页
    print(f"正在爬第 {i} 页")
    job_cards = driver.find_elements(By.CLASS_NAME, 'list__item__wrap')
    for job in job_cards:
        try:
            title = job.find_element(By.CLASS_NAME, "p-top__1").text
            salary = job.find_element(By.CLASS_NAME, "p-bom__1").text
            company = job.find_element(By.CLASS_NAME, "company__2A8S").text
            detail = job.find_element(By.CLASS_NAME, "p-bom__2").text
            jobs.append({
                "岗位": title,
                "公司": company,
                "薪资": salary,
                "详情": detail
            })
        except:
            continue
    try:
        next_button = driver.find_element(By.CLASS_NAME, 'pager_next')
        if "disabled" in next_button.get_attribute("class"):
            break
        else:
            next_button.click()
            time.sleep(3)
    except:
        break

driver.quit()

# 输出结果
df = pd.DataFrame(jobs)
df.to_excel("拉勾实习岗位.xlsx", index=False)
print("✅ 爬取完成，数据已保存为 Excel。")
