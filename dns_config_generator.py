#!/usr/bin/env python3
import sys
import uuid
import datetime
import plistlib
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLabel, QLineEdit, QPushButton,
                           QComboBox, QCheckBox, QListWidget, QMessageBox,
                           QFileDialog, QGroupBox)
import subprocess
import tempfile
import os
from PyQt6.QtCore import Qt, QTranslator, QLocale
from PyQt6.QtGui import QIcon

class DNSConfigGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.translator = QTranslator()
        self.current_lang = 'zh_TW'
        self.lang_map = {
            '繁體中文': 'zh_TW',
            'English': 'en',
            '日本語': 'ja'
        }
        self.setWindowTitle(self.tr("DNS 設定檔生成器"))
        self.setGeometry(100, 100, 800, 600)

        # 創建中央部件和主佈局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 語言切換
        lang_layout = QHBoxLayout()
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["繁體中文", "English", "日本語"])
        self.lang_combo.currentTextChanged.connect(self.change_language)
        self.lang_label = QLabel(self.tr("語言切換:"))
        lang_layout.addWidget(self.lang_label)
        lang_layout.addWidget(self.lang_combo)
        main_layout.addLayout(lang_layout)

        # DNS 伺服器配置
        dns_group = QWidget()
        dns_layout = QVBoxLayout(dns_group)

        # DNS 類型選擇
        type_layout = QHBoxLayout()
        self.dns_type = QComboBox()
        self.dns_type.addItems([
            self.tr("DNS over HTTPS"),
            self.tr("DNS over TLS"),
            self.tr("DNS over HTTPS/3")
        ])
        self.dns_type.currentTextChanged.connect(self.on_dns_type_changed)
        self.dns_type_label = QLabel(self.tr("DNS 類型:"))
        type_layout.addWidget(self.dns_type_label)
        type_layout.addWidget(self.dns_type)
        dns_layout.addLayout(type_layout)

        # 伺服器 URL/主機名
        server_layout = QHBoxLayout()
        self.server_input = QLineEdit()
        self.server_label = QLabel(self.tr("伺服器 URL/主機名:"))
        server_layout.addWidget(self.server_label)
        server_layout.addWidget(self.server_input)
        dns_layout.addLayout(server_layout)

        # 自定義 IP（可選）
        ip_layout = QHBoxLayout()
        self.ip_input = QLineEdit()
        self.ip_checkbox = QCheckBox(self.tr("使用自定義 IP（可選）:"))
        ip_layout.addWidget(self.ip_checkbox)
        ip_layout.addWidget(self.ip_input)
        dns_layout.addLayout(ip_layout)
        
        # SSID 排除清單
        ssid_group = QWidget()
        ssid_layout = QVBoxLayout(ssid_group)
        
        ssid_header = QHBoxLayout()
        self.ssid_input = QLineEdit()
        self.add_ssid_btn = QPushButton(self.tr("添加 SSID"))
        self.ssid_label = QLabel(self.tr("排除的 SSID:"))
        ssid_header.addWidget(self.ssid_label)
        ssid_header.addWidget(self.ssid_input)
        ssid_header.addWidget(self.add_ssid_btn)
        
        self.ssid_list = QListWidget()
        self.remove_ssid_btn = QPushButton(self.tr("刪除選中的 SSID"))
        
        ssid_layout.addLayout(ssid_header)
        ssid_layout.addWidget(self.ssid_list)
        ssid_layout.addWidget(self.remove_ssid_btn)
        
        # 配置檔案名稱和標識符
        profile_group = QWidget()
        profile_layout = QVBoxLayout(profile_group)
        
        name_layout = QHBoxLayout()
        self.profile_name_label = QLabel(self.tr("設定檔名稱:"))
        self.profile_name = QLineEdit(self.tr("自定義 DNS 設定"))
        name_layout.addWidget(self.profile_name_label)
        name_layout.addWidget(self.profile_name)
        
        identifier_layout = QHBoxLayout()
        self.profile_identifier_label = QLabel(self.tr("設定檔標識符:"))
        self.profile_identifier = QLineEdit(self.tr("com.custom.dns.profile"))
        identifier_layout.addWidget(self.profile_identifier_label)
        identifier_layout.addWidget(self.profile_identifier)

        description_layout = QHBoxLayout()
        self.profile_description_label = QLabel(self.tr("設定檔描述:"))
        self.dns_description = QLineEdit(self.tr("自定義 DNS 設定"))
        description_layout.addWidget(self.profile_description_label)
        description_layout.addWidget(self.dns_description)
        
        # 輸出目錄選擇
        output_layout = QHBoxLayout()
        self.output_label = QLabel(self.tr("輸出目錄:"))
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText(self.tr("選擇輸出目錄"))
        self.output_btn = QPushButton(self.tr("瀏覽..."))
        self.output_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(self.output_btn)
        
        profile_layout.addLayout(name_layout)
        profile_layout.addLayout(identifier_layout)
        profile_layout.addLayout(description_layout)
        profile_layout.addLayout(output_layout)
        
        # 簽名選項
        signing_group = QWidget()
        signing_layout = QVBoxLayout(signing_group)
        
        self.sign_checkbox = QCheckBox(self.tr("使用證書簽名設定檔"))
        signing_layout.addWidget(self.sign_checkbox)
        
        # 證書選擇部分
        self.cert_group = QGroupBox()
        self.cert_group.setObjectName("cert_group")  # 设置对象名以便后续查找
        cert_layout = QVBoxLayout()

        # CA Bundle（必需）
        ca_bundle_layout = QHBoxLayout()
        self.ca_bundle_path = QLineEdit()
        self.ca_bundle_path.setPlaceholderText(self.tr("選擇CA Bundle證書 (.ca-bundle)"))
        self.ca_bundle_btn = QPushButton(self.tr("瀏覽..."))
        self.ca_bundle_btn.clicked.connect(self.browse_ca_bundle)
        ca_bundle_layout.addWidget(QLabel(self.tr("CA Bundle:")))
        ca_bundle_layout.addWidget(self.ca_bundle_path)
        ca_bundle_layout.addWidget(self.ca_bundle_btn)

        # CRT證書（必需）
        crt_layout = QHBoxLayout()
        self.crt_path = QLineEdit()
        self.crt_path.setPlaceholderText(self.tr("選擇CRT證書 (.crt)"))
        self.crt_btn = QPushButton(self.tr("瀏覽..."))
        self.crt_btn.clicked.connect(self.browse_crt)
        self.crt_label = QLabel(self.tr("CRT證書:"))
        crt_layout.addWidget(self.crt_label)
        crt_layout.addWidget(self.crt_path)
        crt_layout.addWidget(self.crt_btn)

        # P7B證書（可選）
        p7b_layout = QHBoxLayout()
        self.p7b_path = QLineEdit()
        self.p7b_path.setPlaceholderText(self.tr("選擇P7B證書 (.p7b) 可選"))
        self.p7b_btn = QPushButton(self.tr("瀏覽..."))
        self.p7b_btn.clicked.connect(self.browse_p7b)
        self.p7b_label = QLabel(self.tr("P7B證書:"))
        p7b_layout.addWidget(self.p7b_label)
        p7b_layout.addWidget(self.p7b_path)
        p7b_layout.addWidget(self.p7b_btn)

        # 私鑰文件（必需）
        key_layout = QHBoxLayout()
        self.key_path = QLineEdit()
        self.key_path.setPlaceholderText(self.tr("選擇私鑰文件 (.key/.txt)"))
        self.key_btn = QPushButton(self.tr("瀏覽..."))
        self.key_btn.clicked.connect(self.browse_key)
        self.key_label = QLabel(self.tr("私鑰文件:"))
        key_layout.addWidget(self.key_label)
        key_layout.addWidget(self.key_path)
        key_layout.addWidget(self.key_btn)

        # 密碼輸入和顯示按鈕佈局
        password_layout = QHBoxLayout()
        self.key_password = QLineEdit()
        self.key_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_password.setPlaceholderText(self.tr("輸入私鑰密碼（可選）"))
        self.toggle_password_btn = QPushButton(self.tr("顯示"))
        self.toggle_password_btn.setCheckable(True)
        self.toggle_password_btn.toggled.connect(self.toggle_password_visibility)
        password_layout.addWidget(self.key_password)
        password_layout.addWidget(self.toggle_password_btn)

        # 組合所有元素
        cert_layout.addLayout(ca_bundle_layout)
        cert_layout.addLayout(crt_layout)
        cert_layout.addLayout(p7b_layout)
        cert_layout.addLayout(key_layout)
        cert_layout.addLayout(password_layout)
        self.cert_group.setLayout(cert_layout)
        signing_layout.addWidget(self.cert_group)
        
        # 將所有部件添加到主佈局
        main_layout.addWidget(dns_group)
        main_layout.addWidget(ssid_group)
        main_layout.addWidget(profile_group)
        main_layout.addWidget(signing_group)

        # 保证按钮是self.generate_btn
        self.generate_btn = QPushButton(self.tr("生成設定檔"))
        main_layout.addWidget(self.generate_btn)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        
        # 連接信號槽
        self.add_ssid_btn.clicked.connect(self.add_ssid)
        self.remove_ssid_btn.clicked.connect(self.remove_ssid)
        self.generate_btn.clicked.connect(self.generate_config)
        self.ip_checkbox.toggled.connect(self.ip_input.setEnabled)
        self.ip_input.setEnabled(False)
        
        # 簽名相關信號連接
        self.sign_checkbox.toggled.connect(self.toggle_signing_options)
        
        # 初始化時禁用所有證書相關控件
        self.cert_group.setEnabled(False)
        self.sign_checkbox.setChecked(False)
        
    def add_ssid(self):
        ssid = self.ssid_input.text().strip()
        if ssid:
            self.ssid_list.addItem(ssid)
            self.ssid_input.clear()
            
    def remove_ssid(self):
        current_item = self.ssid_list.currentItem()
        if current_item:
            self.ssid_list.takeItem(self.ssid_list.row(current_item))
    
    def toggle_signing_options(self, enabled):
        # 启用/禁用整个证书配置组
        for widget in self.findChildren(QGroupBox, "cert_group"):
            widget.setEnabled(enabled)
    
    def browse_ca_bundle(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "選擇 CA Bundle 證書",
            "",
            "CA Bundle (*.crt *.pem *.ca-bundle);;所有文件 (*.*)"
        )
        if file_name:
            self.ca_bundle_path.setText(file_name)

    def browse_crt(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "選擇 CRT 證書",
            "",
            "CRT 證書 (*.crt);;所有文件 (*.*)"
        )
        if file_name:
            self.crt_path.setText(file_name)

    def browse_p7b(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "選擇 P7B 證書",
            "",
            "P7B 證書 (*.p7b);;所有文件 (*.*)"
        )
        if file_name:
            self.p7b_path.setText(file_name)

    def browse_key(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "選擇私鑰文件",
            "",
            "私鑰文件 (*.txt *.key);;所有文件 (*.*)"
        )
        if file_name:
            self.key_path.setText(file_name)
    
    def browse_output_dir(self):
        dir_name = QFileDialog.getExistingDirectory(
            self,
            "選擇輸出目錄",
            "")
        if dir_name:
            self.output_path.setText(dir_name)
    
    def sign_configuration(self, config_file, temp_config):
        crt = self.crt_path.text()
        key = self.key_path.text()
        
        if not all([crt, key]):
            raise Exception("請提供必要的證書文件（CRT 和私鑰）")
        
        # 智能處理證書鏈
        p7b_file = self.p7b_path.text()
        ca_bundle = self.ca_bundle_path.text()
        
        if not all([crt, key]):
            raise Exception("請提供必要的證書文件（CRT 和私鑰）")
            
        # 在當前目錄生成證書鏈文件
        output_dir = os.path.dirname(config_file)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        combined_pem = os.path.join(output_dir, f"combined_{timestamp}.pem")
        
        try:
            # 步驟1：轉換P7B到PEM（與手動命令完全一致）
            p7b_cmd = f'openssl pkcs7 -in "{p7b_file}" -print_certs -out "{combined_pem}"'
            print(f"執行P7B轉換命令：{p7b_cmd}")
            subprocess.run(p7b_cmd, shell=True, check=True)
            
            # 步驟2：追加CA Bundle（與手動命令完全一致）
            if ca_bundle and os.path.exists(ca_bundle):
                with open(combined_pem, 'a') as f:
                    with open(ca_bundle, 'r') as bundle:
                        f.write('\n' + bundle.read())
            
            # 驗證證書鏈
            verify_cmd = f'openssl verify -untrusted "{combined_pem}" "{crt}"'
            print(f"驗證證書鏈：{verify_cmd}")
            verify_result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True)
            if verify_result.returncode != 0:
                raise Exception(f"證書鏈驗證失敗：{verify_result.stderr}")
            
            # 執行簽名（與手動命令完全一致，移除-md sha256參數）
            sign_cmd = (
                f'openssl smime -sign '
                f'-in "{temp_config}" '
                f'-out "{config_file}" '
                f'-signer "{combined_pem}" '
                f'-inkey "{key}" '
                f'-certfile "{combined_pem}" '
                f'-outform der -nodetach'
            )
            print(f"執行簽名命令：{sign_cmd}")
            sign_result = subprocess.run(sign_cmd, shell=True, capture_output=True, text=True)
            
            if sign_result.returncode != 0:
                raise Exception(
                    f"簽名失敗（代碼{sign_result.returncode}）:\n"
                    f"命令：{sign_cmd}\n"
                    f"錯誤輸出：{sign_result.stderr}\n"
                    f"證書鏈文件：{combined_pem}"
                )
                
            print(f"成功生成簽名配置文件：{config_file}")
            print(f"使用的證書鏈文件：{combined_pem}")
            
        except Exception as e:
            if os.path.exists(combined_pem):
                print(f"保留證書鏈文件供調試：{combined_pem}")
            raise Exception(f"配置文件簽名失敗：{str(e)}")
            
    def on_dns_type_changed(self, text):
        # 當DNS類型改變時更新UI提示
        if text == "DNS over HTTPS/3":
            QMessageBox.information(self, "DNS over HTTPS/3 信息",
                                "DNS over HTTPS/3 需要 iOS 15+ 或 macOS 12+ 才能使用。\n" +
                                "確保你的DNS伺服器支持 HTTP/3 協議。")

    def toggle_password_visibility(self, checked):
        if checked:
            self.key_password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_btn.setText("隱藏")
        else:
            self.key_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_btn.setText("顯示")
            
    def change_language(self, lang_text):
        print("切换到语言:", lang_text)
        lang_code = self.lang_map.get(lang_text, 'zh_TW')
        # 兼容 PyInstaller 與開發環境
        import sys
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        qm_path = os.path.join(base_path, 'translations', f'{lang_code}.qm')
        print(f"加载文件: {qm_path}")
        if os.path.exists(qm_path):
            QApplication.instance().removeTranslator(self.translator)
            loaded = self.translator.load(qm_path)
            print(f"加载结果: {loaded}")
            QApplication.instance().installTranslator(self.translator)
            self.current_lang = lang_code
        else:
            print(f"找不到语言文件: {qm_path}")
        self.retranslateUi()
        
    def retranslateUi(self):
        print("retranslateUi 被调用，当前语言:", self.current_lang)
        self.setWindowTitle(self.tr("DNS 設定檔生成器"))
        self.lang_label.setText(self.tr("語言切換:"))
        self.dns_type_label.setText(self.tr("DNS 類型:"))
        self.server_label.setText(self.tr("伺服器 URL/主機名:"))
        self.ssid_label.setText(self.tr("排除的 SSID:"))
        self.ip_checkbox.setText(self.tr("使用自定義 IP（可選）:"))
        self.ssid_input.setPlaceholderText(self.tr("排除的 SSID:"))
        self.add_ssid_btn.setText(self.tr("添加 SSID"))
        self.remove_ssid_btn.setText(self.tr("刪除選中的 SSID"))
        self.profile_name_label.setText(self.tr("設定檔名稱:"))
        self.profile_identifier_label.setText(self.tr("設定檔標識符:"))
        self.profile_description_label.setText(self.tr("設定檔描述:"))
        self.profile_name.setText(self.tr("自定義 DNS 設定"))
        self.dns_description.setText(self.tr("自定義 DNS 設定"))
        self.output_label.setText(self.tr("輸出目錄:"))
        self.output_path.setPlaceholderText(self.tr("選擇輸出目錄"))
        self.output_btn.setText(self.tr("瀏覽..."))
        self.ca_bundle_btn.setText(self.tr("瀏覽..."))
        self.crt_btn.setText(self.tr("瀏覽..."))
        self.p7b_btn.setText(self.tr("瀏覽..."))
        self.key_btn.setText(self.tr("瀏覽..."))
        self.crt_label.setText(self.tr("CRT證書:"))
        self.p7b_label.setText(self.tr("P7B證書:"))
        self.key_label.setText(self.tr("私鑰文件:"))
        self.cert_group.setTitle(self.tr("證書配置"))
        self.sign_checkbox.setText(self.tr("使用證書簽名設定檔"))
        self.ca_bundle_path.setPlaceholderText(self.tr("選擇CA Bundle證書 (.ca-bundle)"))
        self.crt_path.setPlaceholderText(self.tr("選擇CRT證書 (.crt)"))
        self.p7b_path.setPlaceholderText(self.tr("選擇P7B證書 (.p7b) 可選"))
        self.key_path.setPlaceholderText(self.tr("選擇私鑰文件 (.key/.txt)"))
        self.key_password.setPlaceholderText(self.tr("輸入私鑰密碼（可選）"))
        self.toggle_password_btn.setText(self.tr("顯示"))
        self.generate_btn.setText(self.tr("生成設定檔"))

    def generate_config(self):
        try:
            server = self.server_input.text().strip()
            if not server:
                raise ValueError("Server URL/Hostname is required")
                
            # 創建基礎配置
            dns_type = self.dns_type.currentText()
            if dns_type == "DNS over HTTPS/3":
                protocol = "HTTPS"
                server_key = "ServerURL"
                additional_settings = {"ServerHTTPVersion": "3"}
            elif dns_type == "DNS over HTTPS":
                protocol = "HTTPS"
                server_key = "ServerURL"
                additional_settings = {}
            else:  # DNS over TLS
                protocol = "TLS"
                server_key = "ServerName"
                additional_settings = {}

            dns_settings = {
                "DNSProtocol": protocol,
                server_key: server
            }
            dns_settings.update(additional_settings)

            dns_payload_uuid = str(uuid.uuid4())
            config = {
                "PayloadContent": [{
                    "PayloadType": "com.apple.dnsSettings.managed",
                    "PayloadVersion": 1,
                    "PayloadIdentifier": f"com.apple.dnsSettings.managed.{dns_payload_uuid}",
                    "PayloadUUID": dns_payload_uuid,
                    "PayloadDisplayName": self.profile_name.text(),
                    "PayloadDescription": self.dns_description.text(),
                    "PayloadName": self.profile_name.text(),
                    "DNSSettings": dns_settings
                }],
                "PayloadDisplayName": self.profile_name.text(),
                "PayloadIdentifier": self.profile_identifier.text(),
                "PayloadRemovalDisallowed": False,
                "PayloadType": "Configuration",
                "PayloadUUID": str(uuid.uuid4()),
                "PayloadVersion": 1,
                "PayloadName": self.profile_name.text(),
                "PayloadDescription": self.dns_description.text()
            }
            
            # 如果指定了自定義 IP，則添加
            if self.ip_checkbox.isChecked() and self.ip_input.text().strip():
                config["PayloadContent"][0]["DNSSettings"]["ServerAddresses"] = [self.ip_input.text().strip()]

            # 添加 OnDemand 規則
            excluded_ssids = [self.ssid_list.item(i).text() for i in range(self.ssid_list.count())]
            on_demand_rules = [
                # SSID 排除規則
                {
                    "Action": "Disconnect",
                    "SSIDMatch": excluded_ssids
                } if excluded_ssids else None,
                # WiFi 連接規則
                {
                    "Action": "Connect",
                    "InterfaceTypeMatch": "WiFi"
                },
                # 蒙蒙連接規則
                {
                    "Action": "Connect",
                    "InterfaceTypeMatch": "Cellular"
                },
                # 預設斷開規則
                {
                    "Action": "Disconnect"
                }
            ]
            
            # 移除空的 SSID 規則
            on_demand_rules = [rule for rule in on_demand_rules if rule is not None]
            
            # 將規則添加到配置中
            config["PayloadContent"][0]["OnDemandRules"] = on_demand_rules

            # 檢查輸出路徑
            if not self.output_path.text().strip():
                QMessageBox.critical(self, "錯誤", "請選擇輸出目錄")
                return
                
            # 生成未簽名的配置文件
            filename = f"{self.profile_name.text().replace(' ', '_')}.mobileconfig"
            target_dir = self.output_path.text().strip()
            full_path = os.path.join(target_dir, filename)
            
            try:
                with open(full_path, 'wb') as f:
                    plistlib.dump(config, f)
            except Exception as e:
                QMessageBox.critical(self, "錯誤", f"無法寫入文件，請確保目錄可寫。\n目標目錄：{target_dir}\n錯誤信息：{str(e)}")
                return
            
            # 如果需要簽名，生成簽名版本
            if self.sign_checkbox.isChecked():
                try:
                    signed_filename = f"{self.profile_name.text().replace(' ', '_')}_signed.mobileconfig"
                    signed_full_path = os.path.join(target_dir, signed_filename)
                    self.sign_configuration(signed_full_path, full_path)
                    QMessageBox.information(self, "成功", 
                        f"已生成未簽名的配置文件：'{filename}'"
                        f"\n已生成簽名的配置文件：'{signed_filename}'"
                        f"\n文件位置：{target_dir}")
                except Exception as e:
                    QMessageBox.critical(self, "簽名錯誤", f"配置文件簽名失敗：{str(e)}")
            else:
                QMessageBox.information(self, "成功", 
                    f"已生成配置文件：'{filename}'"
                    f"\n文件位置：{target_dir}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DNSConfigGenerator()
    window.show()
    sys.exit(app.exec())
