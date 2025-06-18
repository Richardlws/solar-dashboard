import time
from datetime import datetime,timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# 出发地与目的地
FROM = '上海'
TO = '徐州东'

# 日期：今天
today_str = datetime.today().strftime('%Y-%m-%d')

# 初始化 Chrome 浏览器
def init_browser():
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=options)
    return driver

# 手动扫码登录流程
def manual_login(driver):
    driver.get('https://kyfw.12306.cn/otn/resources/login.html')
    print("🚨 请扫码登录12306账号")
    while True:
        if "我的12306" in driver.page_source:
            print("✅ 登录成功！")
            break
        time.sleep(1)

# 查询车票并尝试预订
def search_ticket(driver):
    driver.get("https://kyfw.12306.cn/otn/leftTicket/init")
    time.sleep(1)

    # 输入出发地
    from_input = driver.find_element(By.ID, "fromStationText")
    from_input.click()
    from_input.send_keys(Keys.CONTROL + "a")
    from_input.send_keys(FROM)
    from_input.send_keys(Keys.ENTER)

    # 输入目的地
    to_input = driver.find_element(By.ID, "toStationText")
    to_input.click()
    to_input.send_keys(Keys.CONTROL + "a")
    to_input.send_keys(TO)
    to_input.send_keys(Keys.ENTER)

    # 输入日期
    date_input = driver.find_element(By.ID, "train_date")
    date_input.click()
    date_input.send_keys(Keys.CONTROL + "a")
    date_input.send_keys(today_str)
    date_input.send_keys(Keys.ENTER)

    # 点查询按钮
    time.sleep(1)
    driver.find_element(By.ID, "query_ticket").click()
    print(f"🎯 查询 {FROM} → {TO} 的高铁票（{today_str}）...")

    # 刷票循环
    from datetime import datetime, timedelta

    # 刷票循环
    while True:
        time.sleep(0.8)
        try:
            train_rows = driver.find_elements(By.XPATH, "//tbody[@id='queryLeftTable']/tr[not(@datatran)]")

            found = False
            for row in train_rows:
                try:
                    # 发车时间列（出发时间一般在 <td class="start-t"> 标签中）
                    start_time_str = row.find_element(By.CLASS_NAME, "start-t").text.strip()
                    if not start_time_str:
                        continue

                    # 转为 datetime 格式（今天的某个时间）
                    start_time = datetime.strptime(today_str + " " + start_time_str, "%Y-%m-%d %H:%M")
                    now = datetime.now()

                    # 如果发车时间距离现在少于 4 小时，跳过
                    if start_time - now < timedelta(hours=4):
                        print(f"⏩ 跳过 {start_time_str} 的车次（小于4小时）")
                        continue

                    # 找“预订”按钮并点击
                    reserve_button = row.find_element(By.XPATH, ".//a[text()='预订']")
                    if reserve_button:
                        print(f"🎯 发现可预订车次，发车时间：{start_time_str}，正在点击...")
                        reserve_button.click()
                        found = True
                        break

                except Exception as inner_e:
                    continue

            if found:
                break
            else:
                print("🔄 未找到合适车次，继续刷新...")
                driver.find_element(By.ID, "query_ticket").click()

        except Exception as e:
            print("⚠️ 报错：", e)


if __name__ == '__main__':
    driver = init_browser()

    try:
        manual_login(driver)
        search_ticket(driver)

    except Exception as e:
        print("❌ 程序出错：", e)

    # ❗不要关闭浏览器
    # driver.quit()
