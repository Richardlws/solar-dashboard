import pickle
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# 出发地与目的地
FROM = '上海'
TO = '徐州东'

# 日期：今天
today_str = datetime.today().strftime('%Y-%m-%d')

# Cookie 文件名
COOKIE_FILE = '12306_cookies.pkl'

# 初始化 Chrome 浏览器
def init_browser():
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=options)
    return driver

# 保存 cookie
def save_cookie(driver):
    cookies = driver.get_cookies()
    with open(COOKIE_FILE, "wb") as f:
        pickle.dump(cookies, f)
    print("✅ Cookie 已保存，下次可自动登录")

# 加载 cookie 实现自动登录
def load_cookie(driver):
    driver.get("https://kyfw.12306.cn/otn/view/index.html")
    with open(COOKIE_FILE, "rb") as f:
        cookies = pickle.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)
    driver.refresh()
    time.sleep(2)
    if "我的12306" in driver.page_source:
        print("✅ 自动登录成功")
    else:
        print("⚠️ Cookie 登录失败，请删除 cookie 文件后重新扫码")

# 手动扫码登录流程
def manual_login(driver):
    driver.get('https://kyfw.12306.cn/otn/resources/login.html')
    print("🚨 请扫码登录12306账号")
    while True:
        if "我的12306" in driver.page_source:
            print("✅ 登录成功！")
            save_cookie(driver)
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
    while True:
        time.sleep(0.8)
        try:
            reserve_buttons = driver.find_elements(By.XPATH, "//a[text()='预订']")
            if reserve_buttons:
                print("🎉 抢到票啦！点击预订中...")
                reserve_buttons[0].click()
                break
            else:
                print("🔄 刷新中，未发现余票")
                driver.find_element(By.ID, "query_ticket").click()
        except Exception as e:
            print("⚠️ 报错：", e)

    print("📝 请手动选择乘客（刘冰）并提交订单，浏览器将保持打开状态")
    input("👉 完成抢票后按 Enter 关闭程序（或直接关闭窗口）")

if __name__ == '__main__':
    driver = init_browser()

    try:
        # 尝试自动登录
        try:
            load_cookie(driver)
        except:
            manual_login(driver)

        search_ticket(driver)

    except Exception as e:
        print("❌ 程序出错：", e)

    # 不自动关闭浏览器
    # driver.quit()
