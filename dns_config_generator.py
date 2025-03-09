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
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

class DNSConfigGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DNS 設定檔生成器")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # DNS 服务器配置
        dns_group = QWidget()
        dns_layout = QVBoxLayout(dns_group)
        
        # DNS 类型选择
        type_layout = QHBoxLayout()
        self.dns_type = QComboBox()
        self.dns_type.addItems(["DNS over HTTPS", "DNS over TLS", "DNS over HTTPS/3"])
        self.dns_type.currentTextChanged.connect(self.on_dns_type_changed)
        type_layout.addWidget(QLabel("DNS 類型:"))
        type_layout.addWidget(self.dns_type)
        dns_layout.addLayout(type_layout)
        
        # 服务器 URL/主机名
        server_layout = QHBoxLayout()
        self.server_input = QLineEdit()
        server_layout.addWidget(QLabel("伺服器 URL/主機名:"))
        server_layout.addWidget(self.server_input)
        dns_layout.addLayout(server_layout)
        
        # 自定义 IP（可选）
        ip_layout = QHBoxLayout()
        self.ip_input = QLineEdit()
        self.ip_checkbox = QCheckBox("使用自定義 IP（可選）:")
        ip_layout.addWidget(self.ip_checkbox)
        ip_layout.addWidget(self.ip_input)
        dns_layout.addLayout(ip_layout)
        
        # SSID 排除列表
        ssid_group = QWidget()
        ssid_layout = QVBoxLayout(ssid_group)
        
        ssid_header = QHBoxLayout()
        self.ssid_input = QLineEdit()
        self.add_ssid_btn = QPushButton("添加 SSID")
        ssid_header.addWidget(QLabel("排除的 SSID:"))
        ssid_header.addWidget(self.ssid_input)
        ssid_header.addWidget(self.add_ssid_btn)
        
        self.ssid_list = QListWidget()
        self.remove_ssid_btn = QPushButton("刪除選中的 SSID")
        
        ssid_layout.addLayout(ssid_header)
        ssid_layout.addWidget(self.ssid_list)
        ssid_layout.addWidget(self.remove_ssid_btn)
        
        # 配置文件名称和标识符
        profile_group = QWidget()
        profile_layout = QVBoxLayout(profile_group)
        
        name_layout = QHBoxLayout()
        self.profile_name = QLineEdit("自定義 DNS 設定")
        name_layout.addWidget(QLabel("設定檔名稱:"))
        name_layout.addWidget(self.profile_name)
        
        identifier_layout = QHBoxLayout()
        self.profile_identifier = QLineEdit("com.custom.dns.profile")
        identifier_layout.addWidget(QLabel("設定檔標識符:"))
        identifier_layout.addWidget(self.profile_identifier)

        description_layout = QHBoxLayout()
        self.dns_description = QLineEdit("自定義 DNS 設定")
        description_layout.addWidget(QLabel("設定檔描述:"))
        description_layout.addWidget(self.dns_description)
        
        # 输出目录选择
        output_layout = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("選擇輸出目錄")
        output_btn = QPushButton("瀏覽...")
        output_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(QLabel("輸出目錄:"))
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(output_btn)
        
        profile_layout.addLayout(name_layout)
        profile_layout.addLayout(identifier_layout)
        profile_layout.addLayout(description_layout)
        profile_layout.addLayout(output_layout)
        
        # 签名选项
        signing_group = QWidget()
        signing_layout = QVBoxLayout(signing_group)
        
        self.sign_checkbox = QCheckBox("使用證書簽名設定檔")
        signing_layout.addWidget(self.sign_checkbox)
        
        # 证书选择部分
        cert_group = QGroupBox("證書配置")
        cert_group.setObjectName("cert_group")  # 设置对象名以便后续查找
        cert_layout = QVBoxLayout()

        # CA Bundle（必需）
        ca_bundle_layout = QHBoxLayout()
        self.ca_bundle_path = QLineEdit()
        self.ca_bundle_path.setPlaceholderText("選擇CA Bundle證書 (.ca-bundle)")
        ca_bundle_btn = QPushButton("瀏覽...")
        ca_bundle_btn.clicked.connect(self.browse_ca_bundle)
        ca_bundle_layout.addWidget(QLabel("CA Bundle:"))
        ca_bundle_layout.addWidget(self.ca_bundle_path)
        ca_bundle_layout.addWidget(ca_bundle_btn)

        # CRT证书（必需）
        crt_layout = QHBoxLayout()
        self.crt_path = QLineEdit()
        self.crt_path.setPlaceholderText("選擇CRT證書 (.crt)")
        crt_btn = QPushButton("瀏覽...")
        crt_btn.clicked.connect(self.browse_crt)
        crt_layout.addWidget(QLabel("CRT證書:"))
        crt_layout.addWidget(self.crt_path)
        crt_layout.addWidget(crt_btn)

        # P7B证书（可选）
        p7b_layout = QHBoxLayout()
        self.p7b_path = QLineEdit()
        self.p7b_path.setPlaceholderText("選擇P7B證書 (.p7b) 可選")
        p7b_btn = QPushButton("瀏覽...")
        p7b_btn.clicked.connect(self.browse_p7b)
        p7b_layout.addWidget(QLabel("P7B證書:"))
        p7b_layout.addWidget(self.p7b_path)
        p7b_layout.addWidget(p7b_btn)

        # 私钥文件（必需）
        key_layout = QHBoxLayout()
        self.key_path = QLineEdit()
        self.key_path.setPlaceholderText("選擇私鑰文件 (.key/.txt)")
        key_btn = QPushButton("瀏覽...")
        key_btn.clicked.connect(self.browse_key)
        key_layout.addWidget(QLabel("私鑰文件:"))
        key_layout.addWidget(self.key_path)
        key_layout.addWidget(key_btn)

        # 密码输入和显示按钮布局
        password_layout = QHBoxLayout()
        self.key_password = QLineEdit()
        self.key_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_password.setPlaceholderText("輸入私鑰密碼（可選）")
        self.toggle_password_btn = QPushButton("顯示")
        self.toggle_password_btn.setCheckable(True)
        self.toggle_password_btn.toggled.connect(self.toggle_password_visibility)
        password_layout.addWidget(self.key_password)
        password_layout.addWidget(self.toggle_password_btn)

        # 组合所有元素
        cert_layout.addLayout(ca_bundle_layout)
        cert_layout.addLayout(crt_layout)
        cert_layout.addLayout(p7b_layout)
        cert_layout.addLayout(key_layout)
        cert_layout.addLayout(password_layout)
        cert_group.setLayout(cert_layout)
        signing_layout.addWidget(cert_group)
        
        # 将所有部件添加到主布局
        main_layout.addWidget(dns_group)
        main_layout.addWidget(ssid_group)
        main_layout.addWidget(profile_group)
        main_layout.addWidget(signing_group)
        main_layout.addWidget(self.sign_checkbox)
        
        # 生成按钮
        self.generate_btn = QPushButton("生成設定檔")
        main_layout.addWidget(self.generate_btn)
        
        # 连接信号槽
        self.add_ssid_btn.clicked.connect(self.add_ssid)
        self.remove_ssid_btn.clicked.connect(self.remove_ssid)
        self.generate_btn.clicked.connect(self.generate_config)
        self.ip_checkbox.toggled.connect(self.ip_input.setEnabled)
        self.ip_input.setEnabled(False)
        
        # 签名相关信号连接
        self.sign_checkbox.toggled.connect(self.toggle_signing_options)
        
        # 初始化时禁用所有证书相关控件
        cert_group.setEnabled(False)
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
            
    def change_language(self, text):
        # 刪除語言切換功能
        pass
    
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
