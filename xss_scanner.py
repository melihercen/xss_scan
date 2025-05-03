# Gerekli kütüphaneleri içe aktar
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException, WebDriverException, NoAlertPresentException
import sys


# XSS testi yapacak ana fonksiyon
def test_xss(url, param_name, payloads, wait_time=5):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') # GUI olmadan çalıştırmak için yorumu kaldırın
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = None
    successful_payloads = []

    print(f"\n[INFO] Hedef URL: {url}")
    print(f"[INFO] Test edilen parametre: {param_name}")
    print(f"[INFO] Yüklenen payload sayısı: {len(payloads)}\n")

    # Payload'ları tek tek dene
    for i, payload in enumerate(payloads):
        if driver is None:
            try:
                print("[INFO] ChromeDriver PATH'de aranıyor...")
                driver = webdriver.Chrome(options=options)
                print("[INFO] WebDriver başarıyla başlatıldı.")

            except WebDriverException as e:
                # Genel WebDriver başlatma hatası
                print(f"[HATA] WebDriver başlatılamadı: {e}")
                return [] # Başlatma hatası ciddi, testi durdur
            except Exception as e:
                 print(f"[HATA] WebDriver başlatılırken beklenmedik bir genel hata oluştu: {e}")
                 return [] # Başlatma hatası ciddi, testi durdur

        # --- Test URL'i oluşturma ve test etme kısmı (Basitleştirilmiş Hata Yakalama ile) ---
        test_url = f"{url}?{param_name}={payload}"
        print(f"[TEST {i+1}/{len(payloads)}] URL: {test_url}")

        try:
            # Sayfayı yükle ve alert bekle
            driver.get(test_url)
            WebDriverWait(driver, wait_time).until(EC.alert_is_present())

            # Alert bulunduysa işlemleri yap
            alert = driver.switch_to.alert
            alert_text = alert.text
            print(f"[BAŞARILI] Alert bulundu! Metin: '{alert_text}'. Payload: {payload}")
            alert.accept()
            successful_payloads.append(payload)

        except (TimeoutException, NoAlertPresentException):
            # WebDriverWait zaman aşımına uğradı VEYA alert'e erişmeye çalışırken bulunamadı.
            # Her iki durumda da beklenen alert tetiklenmedi.
            print(f"[BAŞARISIZ] Alert bulunamadı veya zamanında çıkmadı (Timeout/NoAlert). Payload: {payload}")

        except UnexpectedAlertPresentException as e:
            # Beklenmedik bir anda alert çıktı (belki önceki testten kaldı veya başka bir sebep)
            print(f"[HATA] Beklenmeyen Alert Tespit Edildi: {e}. Payload: {payload}")
            try:
                # Takılı kalan alert'i kapatmayı dene
                alert = driver.switch_to.alert
                alert.accept()
                print("[INFO] Beklenmeyen alert kapatıldı.")
            except NoAlertPresentException:
                pass # Zaten kapanmış olabilir

        except (WebDriverException, Exception) as e:
            # WebDriver ile ilgili bir sorun (tarayıcı çökmesi vb.) VEYA
            # Beklenmedik başka bir Python hatası oluştu.
            print(f"[HATA] Test sırasında hata oluştu ({type(e).__name__}): {e}. Payload: {payload}")
            if driver:
                # Hata durumunda driver'ı kapatmaya çalışmak yerine doğrudan None yapalım
                pass
            driver = None # Bir sonraki payload için yeniden başlatılmasını sağla
            print("[INFO] Hata nedeniyle tarayıcı bir sonraki payload için yeniden başlatılacak.")
            continue # Bu payload'ı atla, sonrakiyle devam et
        
    # Tüm payloadlar denendikten sonra tarayıcıyı kapat
    if driver:
        try:
            driver.quit()
            print("\n[INFO] Tarayıcı kapatıldı.")
        except Exception as e:
            print(f"[UYARI] Tarayıcı kapatılırken hata oluştu: {e}")

    return successful_payloads

# Sonuçları dosyaya kaydetme fonksiyonu (Değişiklik yok)
def save_results(file_path, results):
    """Başarılı payload'ları belirtilen dosyaya kaydeder."""
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write("Muhtemel Başarılı XSS Payloadları\n")
            file.write("=================================\n")
            if results:
                for payload in results:
                    file.write(payload + "\n")
            else:
                file.write("Başarılı payload bulunamadı.\n")
        print(f"\n[INFO] Sonuçlar '{file_path}' dosyasına kaydedildi.")
    except IOError as e:
        print(f"[HATA] Sonuçlar '{file_path}' dosyasına yazılırken bir hata oluştu: {e}")
    except Exception as e:
        print(f"[HATA] Sonuçları kaydederken beklenmedik bir hata oluştu: {e}")


# Payload'ları dosyadan yükleme fonksiyonu (Değişiklik yok)
def load_payloads(file_path):
    """Payload listesini dosyadan okur."""
    payloads = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            payloads = [line.strip() for line in file if line.strip()]
        if not payloads:
             print(f"[UYARI] Payload dosyası '{file_path}' boş veya sadece boş satırlar içeriyor.")
        else:
             print(f"[INFO] '{file_path}' dosyasından {len(payloads)} payload yüklendi.")
        return payloads
    except FileNotFoundError:
        print(f"[HATA] Payload dosyası '{file_path}' bulunamadı.")
        return None
    except Exception as e:
        print(f"[HATA] Payload dosyası okunurken bir hata oluştu: {e}")
        return None

def load_default_payloads(default_file="payload.txt"):
    """Varsayılan payload dosyasını yükler."""
    print(f"[INFO] Varsayılan payload dosyası '{default_file}' deneniyor...")
    return load_payloads(default_file)

if __name__ == "__main__":
    target_url = input("Hedef URL (örn: http://example.com/search): ").strip()
    param_name = input("Test edilecek parametre adı (örn: q): ").strip()
    payload_file = input("Payload dosyasının yolu (boş bırakırsanız 'payload.txt' denenir): ").strip()
    result_file = input("Sonuçların kaydedileceği dosya adı (örn: results.txt): ").strip()

    if not target_url or not param_name or not result_file:
        print("[HATA] Hedef URL, parametre adı ve sonuç dosyası adı boş bırakılamaz.")
        sys.exit(1)

    payloads = None
    if payload_file:
        payloads = load_payloads(payload_file)
    else:
        payloads = load_default_payloads()

    if payloads is None or not payloads:
        print("[HATA] Hiç payload yüklenemedi. Lütfen geçerli bir payload dosyası sağlayın.")
        sys.exit(1)

    successful_payloads = test_xss(target_url, param_name, payloads)

    print("\n==== Test Sonuçları ====")
    if successful_payloads:
        print(f"[ÖZET] {len(successful_payloads)} adet muhtemel başarılı payload bulundu:")
        for payload in enumerate(successful_payloads):
            print(f"  - {payload}")
             
        save_results(result_file, successful_payloads)
    else:
        print("[ÖZET] Hiçbir başarılı (alert tetikleyen) payload bulunamadı.")
        save_results(result_file, [])
