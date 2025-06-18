from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from datetime import datetime

# 站点代码映射（部分）
STATION_CODE = {
    '上海': 'SHH',
    '徐州': 'XCH',
}

# 当前日期
today_str = datetime.today().strftime('%Y-%m-%d')

def login(driver):
    print("打开12306并等待扫码登录...")
    driver.get('https://kyfw.12306.cn/otn/resources/login.html')
    time.sleep(2)
    # 切换到扫码登录
    try:
        driver.find_element(By.CLASS_NAME, 'login-hd-account').click()
    except:
        pass  # 如果默认就是扫码登录可以跳过

    # 等待用户扫码登录
    while True:
        if driver.current_url.startswith('https://kyfw.12306.cn/otn/view/index.html'):
            print("✅ 登录成功！")
            break
        time.sleep(1)

def search_ticket(driver, from_station, to_station, date):
    print("开始查询车票...")

    driver.get('https://kyfw.12306.cn/otn/leftTicket/init')

    # 输入出发地
    from_input = driver.find_element(By.ID, "fromStationText")
    from_input.click()
    from_input.send_keys(Keys.CONTROL + "a")
    from_input.send_keys(from_station)
    from_input.send_keys(Keys.ENTER)

    # 输入目的地
    to_input = driver.find_element(By.ID, "toStationText")
    to_input.click()
    to_input.send_keys(Keys.CONTROL + "a")
    to_input.send_keys(to_station)
    to_input.send_keys(Keys.ENTER)

    # 输入日期
    date_input = driver.find_element(By.ID, "train_date")
    date_input.click()
    date_input.send_keys(Keys.CONTROL + "a")
    date_input.send_keys(date)
    date_input.send_keys(Keys.ENTER)

    # 点击查询
    time.sleep(1)
    driver.find_element(By.ID, "query_ticket").click()

    print("查询成功，正在尝试抢票...")

    # 无限循环点击抢票
    while True:
        try:
            time.sleep(0.8)
            results = driver.find_elements(By.XPATH, "//a[text()='预订']")
            if results:
                print("🎯 有票！尝试点击预订...")
                results[0].click()
                break
            else:
                print("🔄 刷新查询中...")
                driver.find_element(By.ID, "query_ticket").click()
        except Exception as e:
            print("⚠️ 报错：", e)
            time.sleep(1)

    print("🎉 已进入下单页，请选择乘客并提交订单！")

if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=options)

    try:
        login(driver)
        search_ticket(driver, '上海', '徐州', today_str)
    except Exception as e:
        print("程序出错：", e)
    finally:
        pass
