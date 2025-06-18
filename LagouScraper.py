from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

# 无头浏览器可选开关（注释掉可可视化）
chrome_options = Options()
# chrome_options.add_argument("--headless")

driver = webdriver.Chrome(options=chrome_options)

# 拉勾首页（必须先访问才能加载 Cookie）
driver.get("https://www.lagou.com/")
time.sleep(3)

# 搜索“计算机”岗位，全国不限城市
keyword = "计算机"
driver.get(f"https://www.lagou.com/jobs/list_{keyword}?city=全国")
time.sleep(5)

job_list = []

for page in range(1, 4):  # 爬前3页
    print(f"📄 正在爬取第 {page} 页")
    time.sleep(3)

    job_cards = driver.find_elements(By.CLASS_NAME, 'list__item__wrap')

    if not job_cards:
        print("⚠️ 没有找到任何职位卡片，可能被反爬或页面未加载")
        break

    for card in job_cards:
        try:
            title = card.find_element(By.CLASS_NAME, "p-top__1").text.strip()
            company = card.find_element(By.CLASS_NAME, "company__2A8S").text.strip()
            salary = card.find_element(By.CLASS_NAME, "p-bom__1").text.strip()
            detail = card.find_element(By.CLASS_NAME, "p-bom__2").text.strip()
            job_list.append({
                "岗位": title,
                "公司": company,
                "薪资": salary,
                "详情": detail
            })
        except Exception as e:
            print("解析某一项失败：", e)
            continue

    try:
        next_btn = driver.find_element(By.CLASS_NAME, 'pager_next')
        if "disabled" in next_btn.get_attribute("class"):
            print("🔚 到最后一页了")
            break
        next_btn.click()
    except:
        print("❌ 找不到下一页按钮")
        break

driver.quit()

# 保存数据
df = pd.DataFrame(job_list)
df.to_excel("lagou_computer_jobs.xlsx", index=False)
print(f"✅ 共保存 {len(df)} 条计算机相关职位，文件已生成：lagou_computer_jobs.xlsx")
