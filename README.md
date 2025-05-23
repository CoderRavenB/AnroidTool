# AnroidTool
✨ AndroidTool'un Sihirli Özellikleri
Program başladığında seni adım adım yönlendirecek. İşte karşılaşacağın ana menüler ve yapabileceklerin:

# 🌟 1. Cihaz Bilgileri: Telefonunun Kimliği!
Program ilk olarak telefonunla bilgisayarın arasındaki bağlantıyı kontrol edecek. Her şey yolundaysa, cihazının tüm önemli bilgilerini bir rapor gibi karşına serecek:

Üretici, Model, Kod Adı
Android ve MIUI Sürümü
Depolama Alanı ve RAM bilgileri
İşlemci ve Çekirdek Sayısı
Pil Sağlığı ve Şarj Döngüsü (varsa)
Bu bilgileri bilgisayarına rapor olarak kaydetme seçeneği de sunulacak. İstersen "E" tuşuna basarak kaydedebilirsin. Bu raporlar, programın olduğu klasörde device_reports adında yeni bir klasörde saklanacak.

# 🔒 2. Bootloader Kilidi Kontrolü: Telefonun Kilidi Açık mı Kapalı mı?
Bu adım, telefonunun bootloader kilidinin (telefona farklı yazılımlar yüklemeyi sağlayan bir kilit) açık mı kapalı mı olduğunu gösterir.

# Nasıl Yapılır?
Program senden telefonunu Fastboot moduna almanı isteyecek.
Telefonunu kapat, ardından genellikle Ses Kısma (-) tuşu ile Güç tuşuna aynı anda basılı tutarak Fastboot moduna gir. Ekranda "Fastboot" yazısı veya bir robot logosu göreceksin.
Telefonu bilgisayara bağla ve programdaki talimatı takip ederek Enter'a bas.
Program sana kilidin durumunu söyleyecek: AÇIK (unlocked) veya KAPALI (locked).
İşlem bitince telefonunu normal moda yeniden başlatmak isteyip istemediğini soracak. Seçim sana kalmış!

# 📥 3. ROM İndirme Önerisi: Yeni Bir Yazılım İster misin?
Program sana örnek bir ROM (telefon yazılımı) önerecek ve istersen ilgili indirme sayfasına yönlendirecek. "E" dersen, otomatik olarak MIUI'nin resmi indirme sayfası açılacak.

# 🚀 4. Ek Araçlar Menüsü: Daha Fazla Güç Seninle!
Burada telefonunla yapabileceğin diğer harika işlemleri bulacaksın:

1. Ekran Görüntüsü Al: Telefonunun ekran görüntüsünü anında bilgisayarına kaydetmek için harika! Görüntüler screenshots klasörüne gidecek.
2. APK Yükle: Bilgisayarındaki bir uygulamayı (APK dosyası) kolayca telefonuna kurmak için kullanışlı. Sadece APK dosyasının tam yolunu girmen yeterli.
3. Performans Testi: Direkt bir test yapmaz ama telefonunun gücünü ölçmek için Geekbench gibi popüler uygulamaları indirip kullanmanı önerir.
4. Pil Sağlığı Bilgisi: Telefonunun pilinin durumu, döngü sayısı gibi detaylı bilgilere ulaşmanı sağlar.
5. Magisk Uyumluluğu: Telefonun root'luysa (gelişmiş yetkilerle çalışıyorsa) Magisk sürümünü kontrol eder.
6. Cihazı Yeniden Başlatma Seçenekleri: Telefonunu normal, kurtarma (recovery) veya fastboot modunda yeniden başlatabilirsin. Özellikle özel yazılım yüklerken çok işine yarayabilir.
7. Uygulama Yönetimi:
# Tüm Uygulamaları Listele: Telefonundaki bütün uygulamaların teknik adlarını (paket adlarını) listeler.
# Uygulama Kaldır: İstediğin bir uygulamanın paket adını girerek onu telefonundan silebilirsin. Dikkatli ol, önemli sistem uygulamalarını silmemeye özen göster!
