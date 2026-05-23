import json, time, os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ShopeeBot:
    def __init__(self, cookie_path):
        self.cookie_path = cookie_path
        self.driver = None
        self.wait = None

    def login_via_cookie(self):
        if not os.path.exists(self.cookie_path):
            raise FileNotFoundError("Cookie belum dikirim. Kirim teks cookie dulu.")

        opts = Options()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(options=opts)
        self.wait = WebDriverWait(self.driver, 15)

        self.driver.get("https://shopee.co.id")
        time.sleep(3)

        with open(self.cookie_path, 'r') as f:
            cookies = json.load(f)
        for c in cookies:
            if 'domain' in c:
                del c['domain']
            try:
                self.driver.add_cookie(c)
            except:
                pass
        self.driver.refresh()
        time.sleep(5)
        try:
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.shopee-cart-number-badge")
            ))
        except:
            raise Exception("Gagal login. Cookie mungkin expired.")

    def checkout(self, product_url):
        if not self.driver:
            raise Exception("Driver belum aktif.")
        self.driver.get(product_url)
        time.sleep(5)

        try:
            btn = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.btn-solid-primary.btn--l")
            ))
            btn.click()
        except:
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(),'Beli')]")
            btn.click()
        time.sleep(5)

        self._pilih_voucher()

        try:
            order = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(),'Buat Pesanan') or contains(text(),'Checkout')]")
            ))
            order.click()
            time.sleep(3)
            return True
        except Exception as e:
            print(e)
            return False

    def _pilih_voucher(self):
        try:
            items = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.voucher-item"))
            )
            best = None
            best_disc = 0
            for item in items:
                try:
                    txt = item.find_element(By.CSS_SELECTOR, ".voucher-discount").text
                    disc = int(''.join(filter(str.isdigit, txt)))
                    if disc > best_disc:
                        best_disc = disc
                        best = item
                except:
                    continue
            if best:
                best.click()
                time.sleep(2)
                print(f"Voucher terpasang: Rp{best_disc}")
        except:
            pass

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
