import json, time, os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ShopeeBot:
    def __init__(self, cookie_path):
        self.cookie_path = cookie_path
        self.driver = None
        self.wait = None

    def login_via_cookie(self):
        if not os.path.exists(self.cookie_path):
            raise FileNotFoundError("Cookie belum dikirim. Harap kirim file cookie terlebih dahulu.")

        opts = Options()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1280,800")
        
        # PERHATIKAN: Opsi --headless SUDAH DIHAPUS di sini.
        
        opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option('useAutomationExtension', False)
        
        # Jalur disesuaikan dengan lingkungan Ubuntu
        opts.binary_location = "/usr/bin/chromium-browser"
        service = Service("/usr/bin/chromedriver")

        self.driver = webdriver.Chrome(service=service, options=opts)
        
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
                })
            """
        })
        
        self.wait = WebDriverWait(self.driver, 15)

        self.driver.get("https://shopee.co.id")
        time.sleep(3)

        with open(self.cookie_path, 'r') as f:
            cookies = json.load(f)
            
        for c in cookies:
            if 'name' not in c or 'value' not in c:
                continue
            if 'sameSite' in c:
                del c['sameSite']
            if 'domain' in c and not c['domain'].startswith('.'):
                c['domain'] = '.' + c['domain']

            try:
                self.driver.add_cookie({
                    'name': c['name'],
                    'value': c['value'],
                    'domain': c.get('domain', '.shopee.co.id'),
                    'path': c.get('path', '/')
                })
            except Exception:
                pass
                
        self.driver.refresh()
        time.sleep(5)
        
        try:
            bahasa_btn = self.driver.find_element(By.XPATH, "//button[contains(text(),'Bahasa Indonesia')]")
            bahasa_btn.click()
            time.sleep(2)
        except:
            pass

        try:
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.shopee-cart-number-badge")
            ))
        except:
            self.driver.save_screenshot("cctv_error.png")
            raise Exception("Gagal masuk. Mengirim bukti rekaman CCTV...")

    def checkout(self, product_url):
        if not self.driver:
            raise Exception("Pengendali browser belum aktif.")
        self.driver.get(product_url)
        time.sleep(5)

        try:
            btn = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(),'Beli Sekarang')]")
            ))
            btn.click()
        except:
            try:
                btn = self.driver.find_element(By.XPATH, "//button[contains(text(),'Beli')]")
                btn.click()
            except:
                self.driver.save_screenshot("cctv_error.png")
                return False
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
            self.driver.save_screenshot("cctv_error.png")
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
        except:
            pass

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
