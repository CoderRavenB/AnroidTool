import subprocess
import webbrowser
import time
import os
import re
import threading
import itertools
import json

from colorama import Fore, Style, init

# Colorama'yı başlat (Renklerin otomatik sıfırlanması için)
init(autoreset=True)

# --- Renk Kodları Kısayolları (Siyah arka plana göre ayarlandı) ---
HEADER = Fore.WHITE + Style.BRIGHT
SUCCESS = Fore.GREEN + Style.BRIGHT
WARNING = Fore.YELLOW + Style.BRIGHT
ERROR = Fore.RED + Style.BRIGHT
INFO = Fore.LIGHTBLUE_EX
RESET = Style.RESET_ALL
DIM = Style.DIM + Fore.LIGHTBLACK_EX

# --- Animasyon Fonksiyonları ---
stop_animation = False
animation_thread = None

def animate_spinner(message):
    """Basit bir spinner animasyonu gösterir."""
    for char in itertools.cycle(['|', '/', '-', '\\']):
        if stop_animation:
            break
        print(f"\r{INFO}{message} {char}{RESET}", end="", flush=True)
        time.sleep(0.1)
    print(f"\r{INFO}{message} {' ' * 5}{RESET}", end="", flush=True) # Animasyonu temizle

def start_animation(message):
    """Animasyonu başlatır."""
    global stop_animation, animation_thread
    stop_animation = False
    animation_thread = threading.Thread(target=animate_spinner, args=(message,))
    animation_thread.start()

def stop_and_clear_animation():
    """Animasyonu durdurur ve temizler."""
    global stop_animation, animation_thread
    stop_animation = True
    if animation_thread and animation_thread.is_alive():
        animation_thread.join() # İş parçacığının bitmesini bekle
    print("\r" + " " * 80 + "\r", end="", flush=True) # Önceki animasyon satırını tamamen temizle

# --- Yardımcı Komut Çalıştırma Fonksiyonu ---
def run_cmd(cmd, check_error=True):
    """
    Belirtilen komutu çalıştırır ve çıktısını döndürür.
    Hata durumunda mesaj basar ve None döndürür.
    """
    try:
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', check=False)
        if check_error and process.returncode != 0:
            error_message = process.stderr.strip() if process.stderr else "Bilinmeyen Hata"
            print(f"{ERROR}Hata: '{cmd}' komutu başarısız oldu. Çıkış Kodu: {process.returncode}. Hata Mesajı: {error_message}{RESET}")
            return None
        return process.stdout.strip()
    except FileNotFoundError:
        print(f"{ERROR}Hata: '{cmd.split()[0]}' komutu bulunamadı. Lütfen ADB/Fastboot'un sistem PATH'inde olduğundan emin olun.{RESET}")
        return None
    except Exception as e:
        print(f"{ERROR}Beklenmeyen hata oluştu: {e}{RESET}")
        return None

# --- ADB ve Fastboot Bağlantı Kontrolü ve Sürücü Rehberliği ---
def adb_check():
    """
    Sistemde ADB ve Fastboot'un varlığını kontrol eder, cihaz bağlantısını test eder
    ve eksiklik durumunda sürücü rehberliği yapar.
    """
    print(f"{INFO}Temel araçlar kontrol ediliyor: ADB & Fastboot...{RESET}")
    
    adb_ok = False
    fastboot_ok = False

    # ADB kontrolü
    adb_version_output = run_cmd("adb version", check_error=False)
    if adb_version_output is None or "Android Debug Bridge" not in adb_version_output:
        print(f"{ERROR}[X] ADB bulunamadı veya düzgün çalışmıyor.{RESET}")
    else:
        print(f"{SUCCESS}[OK] ADB başarıyla algılandı.{RESET}")
        adb_ok = True

    # Fastboot kontrolü
    fastboot_version_output = run_cmd("fastboot --version", check_error=False)
    if fastboot_version_output is None or "fastboot version" not in fastboot_version_output:
        print(f"{ERROR}[X] Fastboot bulunamadı veya düzgün çalışmıyor.{RESET}")
    else:
        print(f"{SUCCESS}[OK] Fastboot başarıyla algılandı.{RESET}")
        fastboot_ok = True

    if not adb_ok or not fastboot_ok:
        print(f"{WARNING}[!] ADB veya Fastboot eksik/hatalı. Lütfen aşağıdaki adımları kontrol edin:{RESET}")
        print(f"{INFO}  1. Google'ın Platform-Tools paketini indirin: {DIM}https://developer.android.com/tools/releases/platform-tools{RESET}")
        print(f"{INFO}  2. İndirdiğiniz paketi (platform-tools klasörü) kolayca erişebileceğiniz bir yere (örn: C:\\platform-tools) çıkartın.{RESET}")
        print(f"{INFO}  3. Bu klasörü sistem PATH ortam değişkenine ekleyin. (İnternette 'Windows PATH ekleme' olarak aratabilirsiniz.){RESET}")
        print(f"{INFO}  4. USB sürücülerinizin (genellikle 'Google USB Driver') doğru yüklü olduğundan emin olun.{RESET}")
        print(f"{INFO}  5. Bilgisayarınızı yeniden başlatmayı deneyin.{RESET}")
        return False

    start_animation("Cihaz ADB ile bağlantı kuruluyor")
    devices_output = run_cmd("adb devices", check_error=False)
    stop_and_clear_animation()
    
    if devices_output:
        lines = devices_output.splitlines()
        found_device = False
        for line in lines:
            if "device" in line and "offline" not in line and "unauthorized" not in line:
                print(f"{SUCCESS}[OK] Cihaz başarıyla bağlandı!{RESET}")
                found_device = True
                break
            elif "unauthorized" in line:
                print(f"{WARNING}[!] Cihaz yetkilendirilmemiş. Lütfen cihazınızda çıkan ADB yetkilendirme penceresini onaylayın.{RESET}")
                print(f"{INFO}  -> Cihazınızın ayarlarında 'Geliştirici Seçenekleri' altında 'USB Hata Ayıklama'nın açık olduğundan emin olun.{RESET}")
                return False
        if not found_device:
            print(f"{WARNING}[!] Cihaz bağlı değil veya ADB yetkilendirilmemiş. Lütfen kontrol edin:{RESET}")
            print(f"{INFO}  -> Cihazınızın USB kablosunu kontrol edin.{RESET}")
            print(f"{INFO}  -> 'USB Hata Ayıklama' açık mı? (Ayarlar > Geliştirici Seçenekleri){RESET}")
            print(f"{INFO}  -> Cihazınızda çıkan ADB yetkilendirme penceresini onayladınız mı?{RESET}")
            return False
        return True
    else:
        print(f"{WARNING}[!] ADB cihaz çıktısı alınamadı. Cihaz bağlı ve USB Hata Ayıklama açık mı?{RESET}")
        return False

# --- Cihaz Bilgisi Fonksiyonları ---
def get_prop(prop):
    """Belirli bir Android sistem özelliğini (prop) alır."""
    result = run_cmd(f'adb shell getprop {prop}')
    return result if result else "Bilinmiyor"

def get_device_info():
    """Cihazın temel bilgilerini toplar."""
    info = {
        "manufacturer": get_prop("ro.product.manufacturer"),
        "model": get_prop("ro.product.model"),
        "device": get_prop("ro.product.device"),
        "androidVer": get_prop("ro.build.version.release"),
        "romVer": get_prop("ro.build.version.incremental"),
        "miuiVer": get_prop("ro.miui.ui.version.name") or "MIUI değil / Özel ROM",
        "securityPatch": get_prop("ro.build.version.security_patch")
    }

    start_animation("Depolama bilgileri alınıyor")
    storage_info = run_cmd("adb shell df -h /data")
    stop_and_clear_animation()
    if storage_info:
        lines = storage_info.splitlines()
        if len(lines) > 1:
            parts = lines[1].split()
            if len(parts) >= 6:
                info["totalStorage"] = parts[1]
                info["usedStorage"] = parts[2]
                info["availableStorage"] = parts[3]
    
    start_animation("RAM bilgileri alınıyor")
    mem_info = run_cmd("adb shell cat /proc/meminfo")
    stop_and_clear_animation()
    if mem_info:
        mem_total_match = re.search(r"MemTotal:\s*(\d+)\s*kB", mem_info)
        mem_available_match = re.search(r"MemAvailable:\s*(\d+)\s*kB", mem_info)
        if mem_total_match:
            info["totalRAM"] = f"{int(mem_total_match.group(1)) / (1024*1024):.2f} GB"
        if mem_available_match:
            info["availableRAM"] = f"{int(mem_available_match.group(1)) / (1024*1024):.2f} GB"

    start_animation("CPU bilgileri alınıyor")
    cpu_info = run_cmd("adb shell cat /proc/cpuinfo")
    stop_and_clear_animation()
    if cpu_info:
        processor_match = re.search(r"Processor\s*:\s*(.*)", cpu_info)
        if processor_match:
            info["cpuProcessor"] = processor_match.group(1).strip()
        else:
             hardware_match = re.search(r"Hardware\s*:\s*(.*)", cpu_info)
             if hardware_match: info["cpuProcessor"] = hardware_match.group(1).strip()
             else:
                 model_name_match = re.search(r"model name\s*:\s*(.*)", cpu_info)
                 if model_name_match: info["cpuProcessor"] = model_name_match.group(1).strip()

        cpu_cores = len(re.findall(r"processor\s*:\s*\d+", cpu_info))
        if cpu_cores > 0: info["cpuCores"] = cpu_cores
    
    start_animation("Kernel bilgisi alınıyor")
    kernel_version = run_cmd("adb shell uname -r")
    stop_and_clear_animation()
    if kernel_version: info["kernelVersion"] = kernel_version

    # Batarya Sağlığı/Döngü Sayısı (varsa)
    start_animation("Batarya sağlığı kontrol ediliyor")
    battery_info_dumpsys = run_cmd("adb shell dumpsys battery")
    stop_and_clear_animation()
    if battery_info_dumpsys:
        health_match = re.search(r"health:\s*(.*)", battery_info_dumpsys)
        if health_match:
            info["batteryHealth"] = health_match.group(1).strip()
        
        cycle_count = run_cmd("adb shell cat /sys/class/power_supply/battery/cycle_count", check_error=False)
        if cycle_count:
            info["batteryCycleCount"] = cycle_count.strip()

    return info

def save_device_info(info_dict):
    """Toplanan cihaz bilgilerini bir dosyaya kaydeder."""
    output_dir = "device_reports"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"{INFO}Cihaz raporları için '{output_dir}' klasörü oluşturuldu.{RESET}")

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename_txt = f"device_info_{timestamp}.txt"
    filename_json = f"device_info_{timestamp}.json"
    filepath_txt = os.path.join(output_dir, filename_txt)
    filepath_json = os.path.join(output_dir, filename_json)

    # Metin dosyasına kaydetme
    with open(filepath_txt, "w", encoding="utf-8") as f:
        f.write("--- Cihaz Bilgileri Raporu ---\n\n")
        device_info_map = {
            "manufacturer": "Üretici", "model": "Model", "device": "Cihaz Kodu",
            "androidVer": "Android Sürümü", "romVer": "ROM Versiyonu (Incremental)",
            "miuiVer": "MIUI Versiyonu", "securityPatch": "Güvenlik Yaması",
            "totalStorage": "Toplam Depolama", "usedStorage": "Kullanılan Depolama",
            "availableStorage": "Boş Depolama", "totalRAM": "Toplam RAM",
            "availableRAM": "Boş RAM", "cpuProcessor": "İşlemci",
            "cpuCores": "Çekirdek Sayısı", "kernelVersion": "Kernel Versiyonu",
            "batteryHealth": "Batarya Sağlığı", "batteryCycleCount": "Batarya Döngü Sayısı"
        }
        for k, v in info_dict.items():
            f.write(f"  > {device_info_map.get(k, k)}: {v}\n")
    
    # JSON dosyasına kaydetme
    with open(filepath_json, "w", encoding="utf-8") as f:
        # Renk kodlarını JSON'a kaydetmemek için temizleyelim
        cleaned_info_dict = {k: re.sub(r'\x1b\[[0-9;]*m', '', str(v)) for k, v in info_dict.items()}
        json.dump(cleaned_info_dict, f, indent=4, ensure_ascii=False) # Türkçe karakter desteği

    print(f"{SUCCESS}[OK] Cihaz bilgileri '{filepath_txt}' ve '{filepath_json}' konumlarına kaydedildi.{RESET}")
    print(f"{INFO}Rapor klasörü: {Fore.CYAN}{os.path.abspath(output_dir)}{RESET}")


# --- Bootloader Kilidi Kontrolü ---
def bootloader_status():
    """
    Cihazın Fastboot modundaki bootloader kilidi durumunu kontrol eder.
    Kullanıcıyı Fastboot moduna manuel olarak geçmesi konusunda bilgilendirir.
    """
    print(f"\n{HEADER}--- Bootloader Kilidi Kontrolü ---{RESET}")
    print(f"{INFO}Bu işlem için cihazınızın {Fore.YELLOW}Fastboot modunda{INFO} olması gerekmektedir.{RESET}")
    print(f"{INFO}Lütfen cihazınızı Fastboot moduna alın (genellikle {Fore.YELLOW}Ses Kısma + Güç tuşlarına{INFO} basılı tutarak) ve bilgisayara bağlayın.{RESET}")
    
    input(f"{INFO}Cihazınız Fastboot moduna geçtiğinde ve bağlandığında {Fore.YELLOW}Enter tuşuna basın...{RESET}")

    start_animation("Cihaz Fastboot modunda kontrol ediliyor")
    
    # Cihazın fastboot modunda olup olmadığını kontrol et
    fastboot_devices = run_cmd("fastboot devices", check_error=False)
    stop_and_clear_animation()

    if fastboot_devices and "fastboot" in fastboot_devices:
        print(f"{SUCCESS}[OK] Cihaz fastboot modunda algılandı!{RESET}")
        unlocked_output = run_cmd('fastboot getvar unlocked 2>&1')
        
        reboot_choice = input(f"{INFO}\nCihazı normal moda yeniden başlatmak ister misiniz? ({Fore.YELLOW}E{INFO}/{Fore.YELLOW}H{INFO}): {RESET}").strip().upper()
        if reboot_choice == 'E':
            start_animation("Cihaz normal moda yeniden başlatılıyor")
            run_cmd("fastboot reboot")
            stop_and_clear_animation()
            print(f"{INFO}Cihaz yeniden başlatılıyor...{RESET}")
        else:
            print(f"{INFO}Cihaz Fastboot modunda bırakıldı. Manuel olarak kapatabilirsiniz.{RESET}")

        if unlocked_output:
            match = re.search(r"unlocked:\s*(yes|no)", unlocked_output, re.IGNORECASE)
            if match:
                status = match.group(1).lower()
                if status == "yes":
                    print(f"\nBootloader Kilidi Durumu: {SUCCESS}AÇIK{RESET}")
                else:
                    print(f"\nBootloader Kilidi Durumu: {WARNING}KAPALI{RESET}")
            else:
                print(f"\nBootloader Kilidi Durumu: {ERROR}Bilinmiyor (Çıktı Hatası){RESET}")
        else:
            print(f"\nBootloader Kilidi Durumu: {ERROR}Bilinmiyor (Komut Hatası){RESET}")
    else:
        print(f"{ERROR}[X] Hata: Cihaz Fastboot modunda algılanamadı. Lütfen cihazınızın doğru modda ve bağlı olduğundan emin olun.{RESET}")
        print(f"\nBootloader Kilidi Durumu: {ERROR}Bilinmiyor (Fastboot Hatası - Cihaz Yok){RESET}")


# --- Ekran Görüntüsü Alma ---
def take_screenshot():
    """Cihazdan ekran görüntüsü alır ve kaydeder."""
    print(f"\n{HEADER}--- Ekran Görüntüsü Alma ---{RESET}")
    output_dir = "screenshots"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"{INFO}Ekran görüntüleri için '{output_dir}' klasörü oluşturuldu.{RESET}")

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    filepath = os.path.join(output_dir, filename)

    start_animation("Ekran görüntüsü alınıyor")
    cmd_screenshot = f"adb shell screencap -p /sdcard/{filename}"
    cmd_pull = f"adb pull /sdcard/{filename} {filepath}"
    cmd_delete = f"adb shell rm /sdcard/{filename}"

    result_screenshot = run_cmd(cmd_screenshot)
    if result_screenshot is None:
        stop_and_clear_animation()
        print(f"{ERROR}[X] Ekran görüntüsü cihazda alınamadı. Cihazınızın ekranı açık mı?{RESET}")
        return

    stop_and_clear_animation()
    start_animation(f"Ekran görüntüsü bilgisayara aktarılıyor: {filename}")
    result_pull = run_cmd(cmd_pull)
    if result_pull is None:
        stop_and_clear_animation()
        print(f"{ERROR}[X] Ekran görüntüsü bilgisayara aktarılamadı. (Belki de cihazda yer kalmadı veya izin sorunu var){RESET}")
        run_cmd(cmd_delete)
        return
    
    stop_and_clear_animation()
    run_cmd(cmd_delete)
    
    print(f"{SUCCESS}[OK] Ekran görüntüsü başarıyla alındı ve '{filepath}' konumuna kaydedildi.{RESET}")
    print(f"{INFO}Dosya yolu: {Fore.CYAN}{os.path.abspath(filepath)}{RESET}")


# --- Uygulama Yükleme (APK Sideload) ---
def install_apk():
    """Belirtilen APK dosyasını cihaza yükler."""
    print(f"\n{HEADER}--- APK Yükleme ---{RESET}")
    apk_path = input(f"{INFO}Yüklemek istediğiniz APK dosyasının tam yolunu girin (örn: C:\\Users\\User\\app.apk): {RESET}").strip()

    if not os.path.exists(apk_path):
        print(f"{ERROR}[X] Belirtilen dosya yolu bulunamadı: '{apk_path}'{RESET}")
        return
    if not apk_path.lower().endswith(".apk"):
        confirm = input(f"{WARNING}[!] Belirtilen dosya bir APK dosyası gibi görünmüyor. Devam etmek istiyor musunuz? ({Fore.YELLOW}E{WARNING}/{Fore.YELLOW}H{WARNING}): {RESET}").strip().upper()
        if confirm != 'E':
            print(f"{INFO}APK yükleme iptal edildi.{RESET}")
            return

    start_animation(f"'{os.path.basename(apk_path)}' yükleniyor")
    result = run_cmd(f'adb install "{apk_path}"')
    stop_and_clear_animation()

    if result and "Success" in result:
        print(f"{SUCCESS}[OK] APK başarıyla yüklendi: '{os.path.basename(apk_path)}'{RESET}")
    else:
        print(f"{ERROR}[X] APK yüklenemedi. Hata: {result}{RESET}")
        print(f"{INFO}  -> Cihazınızda 'Bilinmeyen Kaynaklardan Yükleme' izni açık mı?{RESET}")
        print(f"{INFO}  -> APK dosyası bozuk veya cihazınızla uyumsuz olabilir mi?{RESET}")


# --- Yeniden Başlatma Menüsü ---
def reboot_menu():
    """Cihazı farklı modlarda yeniden başlatma seçeneklerini sunar."""
    while True:
        print(f"\n{HEADER}--- Cihazı Yeniden Başlat ---{RESET}")
        print(f"{INFO}[1] Normal Yeniden Başlatma{RESET}")
        print(f"{INFO}[2] Kurtarma Modunda (Recovery) Yeniden Başlatma{RESET}")
        print(f"{INFO}[3] Fastboot Modunda Yeniden Başlatma{RESET}")
        print(f"{INFO}[4] Geri Dön{RESET}")
        
        choice = input(f"{Fore.WHITE}Seçiminiz (1-4): {RESET}").strip()
        
        if not choice.isdigit() or int(choice) not in range(1, 5):
            print(f"{ERROR}[X] Geçersiz seçim. Lütfen 1 ile 4 arasında bir sayı girin.{RESET}")
            continue

        if choice == "1":
            start_animation("Cihaz normal modda yeniden başlatılıyor")
            run_cmd("adb reboot")
            stop_and_clear_animation()
            break
        elif choice == "2":
            start_animation("Cihaz kurtarma modunda yeniden başlatılıyor")
            run_cmd("adb reboot recovery")
            stop_and_clear_animation()
            break
        elif choice == "3":
            start_animation("Cihaz fastboot modunda yeniden başlatılıyor")
            run_cmd("adb reboot bootloader")
            stop_and_clear_animation()
            print(f"{WARNING}Manuel olarak fastboot modundan çıkmanız gerekebilir (genellikle 'fastboot reboot' ile).{RESET}")
            break
        elif choice == "4":
            print(f"{INFO}Yeniden başlatma menüsünden çıkılıyor.{RESET}")
            break


# --- Uygulama Yönetimi Menüsü ---
def app_management_menu():
    """Uygulama yönetimi seçeneklerini sunar (listeleme ve kaldırma)."""
    while True:
        print(f"\n{HEADER}--- Uygulama Yönetimi ---{RESET}")
        print(f"{INFO}[1] Tüm Yüklü Uygulamaları Listele{RESET}")
        print(f"{INFO}[2] Belirli Bir Uygulamayı Kaldır{RESET}")
        print(f"{INFO}[3] Geri Dön{RESET}")

        choice = input(f"{Fore.WHITE}Seçiminiz (1-3): {RESET}").strip()
        
        if not choice.isdigit() or int(choice) not in range(1, 4):
            print(f"{ERROR}[X] Geçersiz seçim. Lütfen 1 ile 3 arasında bir sayı girin.{RESET}")
            continue

        if choice == "1":
            start_animation("Uygulamalar listeleniyor")
            apps = run_cmd("adb shell pm list packages")
            stop_and_clear_animation()
            if apps:
                print(f"{INFO}--- Yüklü Uygulamalar ({len(apps.splitlines())} adet) ---{RESET}")
                for app in apps.splitlines():
                    print(f"  {DIM}- {app.replace('package:', '')}{RESET}")
                print(f"{INFO}------------------------------------{RESET}")
            else:
                print(f"{WARNING}[!] Uygulama listesi alınamadı.{RESET}")
        elif choice == "2":
            package_name = input(f"{Fore.YELLOW}Kaldırmak istediğiniz uygulamanın paket adını girin (örn: com.example.app): {RESET}").strip()
            if package_name:
                confirm = input(f"{WARNING}UYARI: '{package_name}' uygulamasını kaldırmak üzeresiniz. Emin misiniz? ({Fore.YELLOW}E{WARNING}/{Fore.YELLOW}H{WARNING}): {RESET}").strip().upper()
                if confirm == 'E':
                    start_animation(f"'{package_name}' kaldırılıyor")
                    result = run_cmd(f"adb uninstall {package_name}")
                    stop_and_clear_animation()
                    if result and "Success" in result:
                        print(f"{SUCCESS}[OK] '{package_name}' başarıyla kaldırıldı.{RESET}")
                    else:
                        print(f"{ERROR}[X] '{package_name}' kaldırılamadı. Hata: {result}{RESET}")
                else:
                    print(f"{INFO}Kaldırma işlemi iptal edildi.{RESET}")
            else:
                print(f"{WARNING}[!] Geçersiz paket adı.{RESET}")
        elif choice == "3":
            print(f"{INFO}Uygulama yönetimi menüsünden çıkılıyor.{RESET}")
            break

# --- Ana Araç Menüsü ---
def tool_menu():
    """Programın ana araç menüsünü sunar."""
    while True:
        print(f"\n{HEADER}--- Ek Araçlar ---{RESET}")
        print(f"{INFO}[1] Ekran Görüntüsü Al{RESET}")
        print(f"{INFO}[2] APK Yükle{RESET}")
        print(f"{INFO}[3] Performans Testi (Geekbench önerilir){RESET}")
        print(f"{INFO}[4] Pil Sağlığı Bilgisi{RESET}")
        print(f"{INFO}[5] Magisk Uyumluluğu Kontrolü{RESET}") # Metin eski haline getirildi
        print(f"{INFO}[6] Cihazı Yeniden Başlatma Seçenekleri{RESET}")
        print(f"{INFO}[7] Uygulama Yönetimi{RESET}")
        print(f"{INFO}[8] Çıkış{RESET}")

        choice = input(f"{Fore.WHITE}Seçiminiz (1-8): {RESET}").strip()
        
        if not choice.isdigit() or int(choice) not in range(1, 9):
            print(f"{ERROR}[X] Geçersiz seçim. Lütfen 1 ile 8 arasında bir sayı girin.{RESET}")
            continue
        
        if choice == "1":
            take_screenshot()
        elif choice == "2":
            install_apk()
        elif choice == "3":
            print(f"\n{INFO}>> Performans testi için Google Play'den Geekbench gibi bir uygulama indirerek cihazınızda çalıştırın.{RESET}")
        elif choice == "4":
            print(f"\n{HEADER}--- Pil Bilgisi ---{RESET}")
            start_animation("Pil bilgisi alınıyor")
            battery_info_dumpsys = run_cmd("adb shell dumpsys battery")
            stop_and_clear_animation()
            print(battery_info_dumpsys if battery_info_dumpsys else f"{WARNING}[!] Pil bilgisi alınamadı.{RESET}")
        elif choice == "5":
            print(f"\n{INFO}>> Magisk kontrol ediliyor...{RESET}")
            start_animation("Magisk sürümü kontrol ediliyor")
            magisk_version = run_cmd("adb shell su -c 'magisk -v'", check_error=False)
            stop_and_clear_animation()
            if magisk_version and "not found" not in magisk_version.lower() and "permission denied" not in magisk_version.lower():
                print(f"{SUCCESS}[OK] Magisk sürümü: {magisk_version}{RESET}")
            else:
                print(f"{WARNING}[!] Magisk bulunamadı veya root yetkisi verilmedi.{RESET}")
        elif choice == "6":
            reboot_menu()
        elif choice == "7":
            app_management_menu()
        elif choice == "8":
            print(f"{INFO}Ek araçlar menüsünden çıkılıyor.{RESET}")
            break
        print(f"{Fore.MAGENTA}------------------------------------{RESET}")

# --- Ana Program Fonksiyonu ---
def main():
    # Program başlığı ve bilgisi
    print(f"{HEADER}")
    print(f"{SUCCESS}------------------------------------------------------------{RESET}")
    print(f"{HEADER}           A N D R O I D T O O L    v1.1{RESET}")
    print(f"{HEADER}        Bu yazılım forum.miuiturkiye.net için yazıldı.{RESET}")
    print(f"{SUCCESS}------------------------------------------------------------{RESET}\n")

    start_animation("Program başlatılıyor...")
    time.sleep(2) 
    stop_and_clear_animation()
    print(f"{SUCCESS}[OK] AndroidTool hazır!{RESET}\n")

    # ADB ve Fastboot kontrolleri yapılır, başarısız olursa program sonlandırılır
    if not adb_check():
        print(f"{ERROR}Program sonlandırılıyor.{RESET}")
        input(f"{INFO}Devam etmek için {Fore.YELLOW}Enter{INFO} tuşuna basın...{RESET}")
        return

    # Cihaz bilgileri alınır ve gösterilir
    info = get_device_info()
    print(f"\n{HEADER}--- Cihaz Bilgileri ---{RESET}")
    device_info_map = {
        "manufacturer": "Üretici",
        "model": "Model",
        "device": "Cihaz Kodu",
        "androidVer": "Android Sürümü",
        "romVer": "ROM Versiyonu (Incremental)",
        "miuiVer": "MIUI Versiyonu",
        "securityPatch": "Güvenlik Yaması",
        "totalStorage": "Toplam Depolama",
        "usedStorage": "Kullanılan Depolama",
        "availableStorage": "Boş Depolama",
        "totalRAM": "Toplam RAM",
        "availableRAM": "Boş RAM",
        "cpuProcessor": "İşlemci",
        "cpuCores": "Çekirdek Sayısı",
        "kernelVersion": "Kernel Versiyonu",
        "batteryHealth": "Batarya Sağlığı",
        "batteryCycleCount": "Batarya Döngü Sayısı"
    }
    for k, v in info.items():
        if k in device_info_map: # Sadece haritada olanları yazdır
            print(f"{INFO}  > {device_info_map.get(k, k)}: {v}{RESET}")

    # Cihaz bilgilerini kaydetme seçeneği
    save_choice = input(f"{INFO}\nToplanan cihaz bilgilerini kaydetmek ister misiniz? ({Fore.YELLOW}E{INFO}/{Fore.YELLOW}H{INFO}): {RESET}").strip().upper()
    if save_choice == 'E':
        # Root durumu kaldırıldığından, info_dict'ten rootStatus'ı filtrele
        filtered_info = {k: v for k, v in info.items() if k != "rootStatus"}
        save_device_info(filtered_info)
    else:
        print(f"{INFO}Cihaz bilgileri kaydedilmedi.{RESET}")

    # Bootloader kilidi durumu kontrol edilir
    bootloader_status() 

    # ROM önerisi ve indirme seçeneği
    print(f"\n{INFO}Önerilen ROM: MIUI 14.0.7.0 Global Stable (Örnek){RESET}")
    choice = input(f"{Fore.WHITE}Bu ROM'u indirmek ister misiniz? ({Fore.YELLOW}E{Fore.WHITE}/{Fore.YELLOW}H{Fore.WHITE}): {RESET}").strip().upper()
    if choice == "E":
        print(f"{INFO}ROM indirme sayfası açılıyor...{RESET}")
        webbrowser.open("https://bigota.d.miui.com")
    else:
        print(f"{INFO}İndirme işlemi atlandı.{RESET}")

    # Ana araç menüsüne geçiş
    tool_menu()

    # --- Geri Bildirim Süreci ---
    print(f"\n{HEADER}--- Program Sonu ---{RESET}")
    print(f"{INFO}Lütfen bize geri bildirim vererek {Fore.YELLOW}AndroidTool'u{INFO} geliştirmemize yardımcı olun!{RESET}")
    start_animation("Geri bildirim formu açılıyor")
    time.sleep(3)
    stop_and_clear_animation()
    webbrowser.open("https://forms.gle/bNmfHs3HpkZAa3KX8")
    print(f"{SUCCESS}[OK] Tüm işlemler tamamlandı. Güle güle!{RESET}")
    input(f"{INFO}Çıkmak için {Fore.YELLOW}Enter{INFO} tuşuna basın...{RESET}")

# --- Programın Çalıştırılması ---
if __name__ == "__main__":
    main()
