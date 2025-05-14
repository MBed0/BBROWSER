import sys
import os
import json
from PyQt5.QtCore import QUrl, QSize, Qt, QPoint
from PyQt5.QtWidgets import (QApplication, QMainWindow, QToolBar, QLineEdit,
                            QAction, QVBoxLayout, QWidget, QTabWidget, QMenu,
                            QLabel, QDialog, QPushButton, QHBoxLayout,
                            QInputDialog, QMessageBox, QFileDialog, QActionGroup)  # QActionGroup eklendi
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEngineSettings
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineHttpRequest
from PyQt5.QtGui import QIcon, QKeySequence, QDesktopServices


class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()
        self.blocked_urls = []
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    def interceptRequest(self, info):
        # User-Agent değiştirme
        info.setHttpHeader(b"User-Agent", self.user_agent.encode())

        # URL engelleme
        request_url = info.requestUrl().toString()
        for url in self.blocked_urls:
            if url in request_url:
                info.block(True)


class BBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BBROWSER")
        self.setGeometry(100, 100, 1280, 720)
        self.setMinimumSize(800, 600)

        # Profil yönetimi
        self.profiles = {}
        self.current_profile = "default"
        self.incognito = False
        self.load_profiles()

        # Tarayıcı ayarları
        self.interceptor = RequestInterceptor()

        # UI oluştur
        self.init_ui()

        # Varsayılan sayfa
        self.new_tab(QUrl("https://www.google.com"), "Yeni Sekme")

        # Kısayollar
        self.setup_shortcuts()

    def init_ui(self):
        # Ana widget ve layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Sekme yönetimi
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.layout.addWidget(self.tabs)

        # Araç çubuğu
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        # Geri butonu
        self.back_btn = QAction(QIcon.fromTheme("go-previous"), "Geri", self)
        self.back_btn.triggered.connect(lambda: self.current_browser().back())
        self.toolbar.addAction(self.back_btn)

        # İleri butonu
        self.forward_btn = QAction(QIcon.fromTheme("go-next"), "İleri", self)
        self.forward_btn.triggered.connect(lambda: self.current_browser().forward())
        self.toolbar.addAction(self.forward_btn)

        # Yenile butonu
        self.reload_btn = QAction(QIcon.fromTheme("view-refresh"), "Yenile", self)
        self.reload_btn.triggered.connect(lambda: self.current_browser().reload())
        self.toolbar.addAction(self.reload_btn)

        # Ana sayfa butonu
        self.home_btn = QAction(QIcon.fromTheme("go-home"), "Ana Sayfa", self)
        self.home_btn.triggered.connect(self.navigate_home)
        self.toolbar.addAction(self.home_btn)

        # Adres çubuğu
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.toolbar.addWidget(self.url_bar)

        # Yeni sekme butonu
        self.new_tab_btn = QAction(QIcon.fromTheme("tab-new"), "Yeni Sekme", self)
        self.new_tab_btn.triggered.connect(lambda: self.new_tab())
        self.toolbar.addAction(self.new_tab_btn)

        # Gizli sekme butonu
        self.incognito_btn = QAction(QIcon(":incognito.png"), "Gizli Sekme", self)
        self.incognito_btn.triggered.connect(self.new_incognito_tab)
        self.toolbar.addAction(self.incognito_btn)

        # Ayarlar butonu
        self.settings_btn = QAction(QIcon.fromTheme("preferences-system"), "Ayarlar", self)
        self.settings_btn.triggered.connect(self.show_settings)
        self.toolbar.addAction(self.settings_btn)

        # Menü çubuğu
        self.create_menu_bar()

    def create_menu_bar(self):
        menubar = self.menuBar()

        # Dosya menüsü
        file_menu = menubar.addMenu("Dosya")

        new_tab_action = QAction("Yeni Sekme", self)
        new_tab_action.triggered.connect(lambda: self.new_tab())
        file_menu.addAction(new_tab_action)

        new_window_action = QAction("Yeni Pencere", self)
        new_window_action.triggered.connect(self.new_window)
        file_menu.addAction(new_window_action)

        new_incognito_action = QAction("Yeni Gizli Pencere", self)
        new_incognito_action.triggered.connect(self.new_incognito_window)
        file_menu.addAction(new_incognito_action)

        file_menu.addSeparator()

        save_page_action = QAction("Sayfayı Farklı Kaydet...", self)
        save_page_action.triggered.connect(self.save_page)
        file_menu.addAction(save_page_action)

        file_menu.addSeparator()

        exit_action = QAction("Çıkış", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Düzen menüsü
        edit_menu = menubar.addMenu("Düzen")

        find_action = QAction("Bul...", self)
        find_action.triggered.connect(self.find_text)
        edit_menu.addAction(find_action)

        # Görünüm menüsü
        view_menu = menubar.addMenu("Görünüm")

        zoom_in_action = QAction("Yakınlaştır", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Uzaklaştır", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        reset_zoom_action = QAction("Yakınlaştırmayı Sıfırla", self)
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)

        view_menu.addSeparator()

        fullscreen_action = QAction("Tam Ekran", self)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # Araçlar menüsü
        tools_menu = menubar.addMenu("Araçlar")

        dev_tools_action = QAction("Geliştirici Araçları", self)
        dev_tools_action.triggered.connect(self.show_dev_tools)
        tools_menu.addAction(dev_tools_action)

        # Profil menüsü
        profile_menu = menubar.addMenu("Profil")

        self.profile_group = QActionGroup(self)
        for profile_name in self.profiles.keys():
            action = QAction(profile_name, self, checkable=True)
            action.triggered.connect(lambda checked, p=profile_name: self.switch_profile(p))
            profile_menu.addAction(action)
            self.profile_group.addAction(action)
            if profile_name == self.current_profile:
                action.setChecked(True)

        profile_menu.addSeparator()

        new_profile_action = QAction("Yeni Profil Oluştur...", self)
        new_profile_action.triggered.connect(self.create_new_profile)
        profile_menu.addAction(new_profile_action)

        # Yardım menüsü
        help_menu = menubar.addMenu("Yardım")

        about_action = QAction("BBROWSER Hakkında", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_shortcuts(self):
        # Kısayollar
        self.new_tab_shortcut = QAction(self)
        self.new_tab_shortcut.setShortcut(QKeySequence("Ctrl+T"))
        self.new_tab_shortcut.triggered.connect(lambda: self.new_tab())
        self.addAction(self.new_tab_shortcut)

        self.close_tab_shortcut = QAction(self)
        self.close_tab_shortcut.setShortcut(QKeySequence("Ctrl+W"))
        self.close_tab_shortcut.triggered.connect(self.close_current_tab)
        self.addAction(self.close_tab_shortcut)

        self.new_incognito_shortcut = QAction(self)
        self.new_incognito_shortcut.setShortcut(QKeySequence("Ctrl+Shift+N"))
        self.new_incognito_shortcut.triggered.connect(self.new_incognito_tab)
        self.addAction(self.new_incognito_shortcut)

        self.reload_shortcut = QAction(self)
        self.reload_shortcut.setShortcut(QKeySequence("F5"))
        self.reload_shortcut.triggered.connect(lambda: self.current_browser().reload())
        self.addAction(self.reload_shortcut)

        self.dev_tools_shortcut = QAction(self)
        self.dev_tools_shortcut.setShortcut(QKeySequence("F12"))
        self.dev_tools_shortcut.triggered.connect(self.show_dev_tools)
        self.addAction(self.dev_tools_shortcut)

    def current_browser(self):
        return self.tabs.currentWidget()

    def new_tab(self, url=None, title="Yeni Sekme"):
        browser = QWebEngineView()

        if self.incognito:
            profile = QWebEngineProfile("BBROWSER-Incognito")
            settings = profile.settings()
            settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
            settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
            settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, False)
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, False)
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, False)
            web_page = QWebEnginePage(profile, browser)
            browser.setPage(web_page)
        else:
            profile = QWebEngineProfile.defaultProfile()
            profile.setRequestInterceptor(self.interceptor)
            settings = profile.settings()
            settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
            settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
            settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)

        browser.settings().setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        browser.settings().setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)

        if url:
            browser.setUrl(url)
        else:
            browser.setUrl(QUrl("https://www.google.com"))

        index = self.tabs.addTab(browser, title)
        self.tabs.setCurrentIndex(index)

        browser.urlChanged.connect(lambda qurl, browser=browser: self.update_urlbar(qurl, browser))
        browser.loadFinished.connect(lambda _, i=index, browser=browser:
                                     self.tabs.setTabText(i, browser.page().title()[:15]))

        browser.page().fullScreenRequested.connect(self.handle_fullscreen_request)

        return browser

    def new_incognito_tab(self):
        self.incognito = True
        self.new_tab(QUrl("https://www.google.com"), "Gizli Sekme")
        self.incognito = False

    def new_incognito_window(self):
        new_window = BBrowser()
        new_window.incognito = True
        new_window.new_tab(QUrl("https://www.google.com"), "Gizli Sekme")
        new_window.show()

    def new_window(self):
        new_window = BBrowser()
        new_window.show()

    def close_tab(self, index):
        if self.tabs.count() < 2:
            return

        widget = self.tabs.widget(index)
        widget.deleteLater()
        self.tabs.removeTab(index)

    def close_current_tab(self):
        current_index = self.tabs.currentIndex()
        self.close_tab(current_index)

    def navigate_home(self):
        self.current_browser().setUrl(QUrl("https://www.google.com"))

    def navigate_to_url(self):
        q = QUrl(self.url_bar.text())
        if q.scheme() == "":
            q.setScheme("http")

        self.current_browser().setUrl(q)

    def update_urlbar(self, q, browser=None):
        if browser != self.current_browser():
            return

        self.url_bar.setText(q.toString())
        self.url_bar.setCursorPosition(0)

    def show_settings(self):
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("Ayarlar")
        settings_dialog.setModal(True)
        settings_dialog.resize(600, 400)

        layout = QVBoxLayout()

        # Arama motoru ayarı
        search_engine_label = QLabel("Varsayılan Arama Motoru:")
        layout.addWidget(search_engine_label)

        # Giriş sayfası ayarı
        homepage_label = QLabel("Giriş Sayfası:")
        layout.addWidget(homepage_label)

        # Kullanıcı Aracısı ayarı
        user_agent_label = QLabel("Kullanıcı Aracısı:")
        layout.addWidget(user_agent_label)

        # Engellenen siteler
        blocked_sites_label = QLabel("Engellenen Siteler:")
        layout.addWidget(blocked_sites_label)

        # Kaydet ve İptal butonları
        button_layout = QHBoxLayout()
        save_button = QPushButton("Kaydet")
        cancel_button = QPushButton("İptal")
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        settings_dialog.setLayout(layout)
        settings_dialog.exec_()

    def show_dev_tools(self):
        current_browser = self.current_browser()
        current_browser.page().setDevToolsPage(current_browser.page().devToolsPage())
        current_browser.page().triggerAction(QWebEnginePage.InspectElement)

    def find_text(self):
        current_browser = self.current_browser()
        current_browser.page().findText("")

    def zoom_in(self):
        current_browser = self.current_browser()
        current_browser.setZoomFactor(current_browser.zoomFactor() + 0.1)

    def zoom_out(self):
        current_browser = self.current_browser()
        current_browser.setZoomFactor(current_browser.zoomFactor() - 0.1)

    def reset_zoom(self):
        current_browser = self.current_browser()
        current_browser.setZoomFactor(1.0)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def handle_fullscreen_request(self, request):
        request.accept()
        if request.toggleOn():
            self.showFullScreen()
        else:
            self.showNormal()

    def save_page(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self,
                                                   "Sayfayı Kaydet",
                                                   "",
                                                   "HTML Dosyaları (*.html);;Tüm Dosyalar (*)",
                                                   options=options)
        if file_name:
            self.current_browser().page().save(file_name)

    def show_about(self):
        QMessageBox.about(self, "BBROWSER Hakkında",
                          "BBROWSER - Gelişmiş Python Tarayıcı\n\n"
                          "Sürüm: 1.0\n"
                          "PyQt5 ve QtWebEngine kullanılarak geliştirilmiştir.\n\n"
                          "© 2023 BBROWSER Projesi")

    def load_profiles(self):
        # Profilleri yükle (gerçek uygulamada dosyadan okunur)
        self.profiles = {
            "default": {"theme": "light", "homepage": "https://www.google.com"},
            "work": {"theme": "dark", "homepage": "https://www.github.com"},
            "personal": {"theme": "light", "homepage": "https://www.youtube.com"}
        }

    def switch_profile(self, profile_name):
        self.current_profile = profile_name
        QMessageBox.information(self, "Profil Değiştirildi",
                                f"Şu anki profil: {profile_name}")

    def create_new_profile(self):
        name, ok = QInputDialog.getText(self, "Yeni Profil", "Profil Adı:")
        if ok and name:
            if name in self.profiles:
                QMessageBox.warning(self, "Hata", "Bu isimde bir profil zaten var!")
                return

            self.profiles[name] = {"theme": "light", "homepage": "https://www.google.com"}

            # Menüyü güncelle
            menubar = self.menuBar()
            profile_menu = menubar.findChild(QMenu, "Profil")

            action = QAction(name, self, checkable=True)
            action.triggered.connect(lambda checked, p=name: self.switch_profile(p))
            profile_menu.insertAction(profile_menu.actions()[-2], action)
            self.profile_group.addAction(action)

            QMessageBox.information(self, "Başarılı", f"'{name}' profili oluşturuldu!")

    def closeEvent(self, event):
        # Tarayıcı kapanırken yapılacak işlemler
        reply = QMessageBox.question(self, 'Çıkış',
                                     "BBROWSER'ı kapatmak istediğinizden emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("BBROWSER")
    app.setApplicationDisplayName("BBROWSER")
    app.setWindowIcon(QIcon.fromTheme("web-browser"))

    browser = BBrowser()
    browser.show()

    sys.exit(app.exec_())
