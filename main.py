from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.utils import platform
from kivy.core.window import Window
import threading
import socket
import subprocess
import ipaddress
import re
import json
import time
import os
from datetime import datetime

# ============ MAC 厂商数据库 ============
MAC_VENDORS = {
    "00:01:5C": "海康威视", "D0:05:2A": "海康威视", "3C:E5:A6": "海康威视",
    "24:69:68": "海康威视", "D4:6E:0E": "海康威视", "A0:75:91": "海康威视",
    "00:19:0E": "大华", "8C:CA:4E": "大华", "AC:CC:8F": "大华",
    "E0:5A:1F": "大华", "78:2B:CB": "大华",
    "00:1C:8E": "宇视", "48:8E:35": "宇视", "14:9D:09": "宇视",
    "44:39:C4": "宇视",
    "50:3A:AF": "天地伟业", "78:6C:1E": "天地伟业",
    "00:0F:E1": "华为", "B4:0D:0B": "华为", "48:57:02": "华为",
    "C0:61:18": "华为", "50:9A:4C": "华为", "64:16:66": "华为",
    "00:09:6B": "思科", "14:6D:FA": "思科", "70:72:3C": "思科",
    "00:E0:4C": "TP-Link/普联", "B4:68:FC": "TP-Link/普联",
    "C0:4A:00": "TP-Link/普联", "14:CF:92": "TP-Link/普联",
    "A8:5E:4F": "TP-Link/普联", "F8:1A:67": "TP-Link/普联",
    "00:0E:8E": "新华三", "84:47:C6": "新华三", "90:E7:6C": "新华三",
    "C0:00:35": "新华三", "DC:7F:A4": "新华三",
    "00:0C:E5": "锐捷", "18:3A:2D": "锐捷", "10:1F:3E": "锐捷",
    "34:7C:25": "锐捷", "48:E7:DA": "锐捷",
    "98:48:27": "小米", "94:65:2D": "小米", "EC:DF:3A": "小米",
    "E0:3F:49": "华硕", "10:BF:48": "华硕", "04:BF:6D": "华硕",
    "F4:F2:6D": "中兴", "1C:5C:55": "中兴", "44:BE:0C": "中兴",
    "DC:0E:A1": "中兴",
    "00:04:4B": "腾达", "C4:93:D9": "腾达",
    "F0:7D:68": "网件", "6C:5A:B0": "D-Link/友讯",
    "00:0D:88": "深信服", "E0:0F:13": "天融信",
}

# HTTP 指纹识别库
HTTP_FINGERPRINTS = [
    (["hikvision", "ds-", "/doc/page/login.asp", "ivms"], "海康威视", "摄像头"),
    (["dahua", "dh-", "web_service", "login.dsp"], "大华", "摄像头"),
    (["uniview", "ezstation", "unv"], "宇视", "摄像头"),
    (["tiandy", "tc-", "天地伟业"], "天地伟业", "摄像头"),
    (["axis", "axp"], "安讯士", "摄像头"),
    (["huawei", "s5700", "quidway", "cloudengine"], "华为", "交换机"),
    (["cisco", "catalyst", "ios", "nexus"], "思科", "交换机"),
    (["h3c", "comware", "新华三"], "新华三", "交换机"),
    (["tp-link", "tl-s", "jetstream"], "TP-Link/普联", "交换机"),
    (["ruijie", "rg-", "锐捷"], "锐捷", "交换机"),
    (["xiaomi", "miwifi", "redmi"], "小米", "路由器"),
    (["asus", "rt-ac", "rt-ax", "asuswrt"], "华硕", "路由器"),
    (["huawei", "ar-", "netengine", "hg-", "ws-"], "华为", "路由器"),
    (["tp-link", "tl-wr", "tl-wdr", "archer", "deco"], "TP-Link/普联", "路由器"),
    (["h3c", "secpath", "msr", "magic"], "新华三", "路由器"),
    (["zte", "zxhn", "中兴"], "中兴", "路由器"),
    (["tenda"], "腾达", "路由器"),
]

PORT_NAMES = {
    80: "HTTP", 443: "HTTPS", 8080: "HTTP-Alt",
    22: "SSH", 23: "Telnet", 554: "RTSP",
    37777: "海康SDK", 34567: "大华SDK", 8899: "宇视SDK",
    161: "SNMP", 1900: "UPnP", 5060: "SIP", 5000: "UPnP-HTTP",
    7001: "Web设备", 86: "海康CGI",
}


# ============ 扫描引擎 ============
class DeviceScanner:
    def __init__(self):
        self.devices = []
        self.running = False
        self.progress = {"current": 0, "total": 0}

    def get_local_ip(self):
        try:
            if platform == "android":
                from jnius import autoclass
                wm = autoclass('android.net.wifi.WifiManager')
                context = autoclass('org.kivy.android.PythonActivity').mActivity
                wifi = context.getSystemService('wifi')
                dhcp = wifi.getDhcpInfo()
                ip = dhcp.ipAddress
                return f"{(ip & 0xFF)}.{((ip >> 8) & 0xFF)}.{((ip >> 16) & 0xFF)}.{((ip >> 24) & 0xFF)}"
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except:
            return "192.168.1.1"

    def get_network(self):
        ip = self.get_local_ip()
        parts = ip.split(".")
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"

    def ping(self, ip):
        try:
            if platform == "android":
                cmd = ["/system/bin/ping", "-c", "1", "-W", "1", ip]
            else:
                cmd = ["ping", "-c", "1", "-W", "1", ip]
            r = subprocess.run(cmd, capture_output=True, timeout=3)
            return r.returncode == 0
        except:
            return False

    def get_mac(self, ip):
        try:
            self.ping(ip)
            if platform == "android":
                r = subprocess.run(["/system/bin/cat", "/proc/net/arp"],
                                  capture_output=True, text=True, timeout=3)
            else:
                r = subprocess.run(["arp", "-n", ip], capture_output=True, text=True, timeout=3)
            m = re.search(r'([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})',
                         r.stdout, re.I)
            return m.group(1).upper() if m else None
        except:
            return None

    def check_port(self, ip, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            r = s.connect_ex((ip, port))
            s.close()
            return r == 0
        except:
            return False

    def http_fingerprint(self, ip, port=80):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((ip, port))
            req = f"GET / HTTP/1.1\r\nHost: {ip}:{port}\r\nUser-Agent: DeviceScanner/1.0\r\nConnection: close\r\n\r\n"
            s.send(req.encode())
            data = b""
            while True:
                try:
                    c = s.recv(1024)
                    if not c: break
                    data += c
                except: break
            s.close()
            resp = data.decode("utf-8", errors="ignore")
            title = ""
            if "<title>" in resp:
                t = resp.split("<title>")[1].split("</title>")[0]
                title = t.strip()[:60]
            return title
        except:
            return ""

    def identify(self, ip, ports, mac_vendor, http_title):
        type_scores = {"摄像头": 0, "交换机": 0, "路由器": 0}
        brand = mac_vendor or "未知"
        model = "未知"

        # 端口评分
        for p in ports:
            if p in (554, 37777, 34567, 8899, 800):
                type_scores["摄像头"] += 4
            if p in (23, 161):
                type_scores["交换机"] += 3
            if p in (1900, 5000):
                type_scores["路由器"] += 2

        # HTTP 指纹
        full = (http_title + " " + str(ports)).lower()
        best_score = 0
        for kw_list, fp_brand, fp_type in HTTP_FINGERPRINTS:
            score = sum(3 for kw in kw_list if kw in full)
            if score > best_score:
                best_score = score
                if score >= 3:
                    type_scores[fp_type] += score
                    brand = fp_brand
                    for p in [r"(DS-\w+)", r"(DH-\w+)", r"(TL-\w+)", r"(RG-\w+)",
                              r"(RT-\w+)", r"(AR-\d+)", r"(S\d{4})", r"(ZXHN[\w-]+)"]:
                        m = re.search(p, full, re.I)
                        if m: model = m.group(1); break

        # MAC 推断
        if mac_vendor:
            v = mac_vendor.lower()
            if any(k in v for k in ["海康", "hik", "大华", "dahua", "宇视", "uniview", "天地伟业"]):
                type_scores["摄像头"] += 3
            elif any(k in v for k in ["华为", "思科", "h3c", "新华三", "锐捷"]):
                type_scores["交换机"] += 2; type_scores["路由器"] += 1
            elif any(k in v for k in ["tp-link", "小米", "华硕", "中兴", "腾达", "网件"]):
                type_scores["路由器"] += 2

        max_sc = max(type_scores.values())
        dev_type = "未知"
        for t, s in type_scores.items():
            if s == max_sc and s > 0: dev_type = t; break

        confidence = min(max_sc * 25 if max_sc > 0 else 0, 100)
        return dev_type, brand, model, confidence

    def scan_device(self, ip):
        if not self.ping(ip):
            return None

        mac = self.get_mac(ip)
        vendor = ""
        if mac:
            m = mac.upper().replace("-", ":")
            for prefix, name in MAC_VENDORS.items():
                if m.startswith(prefix): vendor = name; break

        ports = [80, 443, 8080, 22, 23, 554, 37777, 34567, 8899, 161, 1900, 5000, 5060, 86]
        open_ports = [p for p in ports if self.check_port(ip, p)]

        http_title = ""
        for p in (80, 443, 8080, 5000):
            if p in open_ports:
                http_title = self.http_fingerprint(ip, p)
                if http_title: break

        dev_type, brand, model, confidence = self.identify(ip, open_ports, vendor, http_title)

        port_names = []
        for p in open_ports[:5]:
            n = PORT_NAMES.get(p, str(p))
            port_names.append(f"{p}({n})")

        return {
            "ip": ip, "mac": mac or "未知", "vendor": vendor or "未知",
            "type": dev_type, "brand": brand, "model": model,
            "confidence": confidence, "ports": open_ports,
            "port_str": ", ".join(port_names), "http_title": http_title
        }

    def scan_network(self, network, callback=None):
        self.devices = []
        self.running = True
        try:
            net = ipaddress.ip_network(network, strict=False)
        except:
            return

        hosts = list(net.hosts())
        total = len(hosts)
        self.progress = {"current": 0, "total": total}

        for ip in hosts:
            if not self.running: break
            self.progress["current"] += 1
            dev = self.scan_device(str(ip))
            if dev:
                self.devices.append(dev)
            if callback:
                Clock.schedule_once(lambda dt, d=dev, p=self.progress, n=total:
                                    callback(d, p["current"], n))

        self.running = False

    def stop(self):
        self.running = False


# ============ Kivy UI ============
class DeviceCard(ButtonBehavior, BoxLayout):
    def __init__(self, device, **kwargs):
        super().__init__(**kwargs)
        self.device = device
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(72)
        self.padding = [dp(12), dp(8)]
        self.spacing = dp(10)

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self._update_rect, size=self._update_rect)

        # 类型图标
        icons = {"摄像头": "📷", "交换机": "🔄", "路由器": "📡"}
        icon_text = icons.get(device["type"], "❓")
        icon = Label(text=icon_text, font_size=dp(26), size_hint=(None, 1), width=dp(40))
        self.add_widget(icon)

        # 信息
        info = BoxLayout(orientation="vertical", spacing=dp(2))
        top = BoxLayout(orientation="horizontal", spacing=dp(8))
        ip_label = Label(text=device["ip"], bold=True, font_size=dp(15),
                         halign="left", size_hint=(None, None), height=dp(20))
        ip_label.bind(texture_size=lambda s, v: setattr(s, "width", v[0] + dp(5)))
        top.add_widget(ip_label)

        type_colors = {"摄像头": "4CAF50", "交换机": "2196F3", "路由器": "FF9800", "未知": "9E9E9E"}
        tc = type_colors.get(device["type"], "999")
        type_label = Label(text=f"[color={tc}]{device['type']}[/color]",
                          markup=True, font_size=dp(12),
                          size_hint=(None, None), height=dp(18))
        type_label.bind(texture_size=lambda s, v: setattr(s, "width", v[0] + dp(5)))
        top.add_widget(type_label)
        top.add_widget(Label())  # 弹簧
        info.add_widget(top)

        brand_label = Label(text=f"{device['brand']}  {device['model']}",
                           font_size=dp(12), color=[.4,.4,.4,1],
                           halign="left", size_hint=(None, None), height=dp(16))
        brand_label.bind(texture_size=lambda s, v: setattr(s, "width", min(v[0] + dp(5), dp(250))))
        info.add_widget(brand_label)

        meta = device.get("port_str", "") or ""
        if meta:
            meta_label = Label(text=meta, font_size=dp(11), color=[.6,.6,.6,1],
                              halign="left", size_hint=(None, None), height=dp(16))
            meta_label.bind(texture_size=lambda s, v: setattr(s, "width", min(v[0] + dp(5), dp(250))))
            info.add_widget(meta_label)
        self.add_widget(info)

        # 置信度
        conf = Label(text=f"{device['confidence']}%",
                     font_size=dp(13), color=[.3,.7,.3,1],
                     bold=True, size_hint=(None, 1), width=dp(40))
        self.add_widget(conf)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_press(self):
        self.show_detail()

    def show_detail(self):
        d = self.device
        lines = [
            f"IP: {d['ip']}",
            f"MAC: {d['mac']}",
            f"厂商: {d['vendor']}",
            "",
            f"类型: {d['type']}",
            f"品牌: {d['brand']}",
            f"型号: {d['model']}",
            f"置信度: {d['confidence']}%",
            "",
            f"开放端口 ({len(d['ports'])}):",
        ]
        for p in d['ports']:
            n = PORT_NAMES.get(p, "未知")
            lines.append(f"  {p} ({n})")

        if d.get("http_title"):
            lines.append("")
            lines.append(f"HTTP: {d['http_title']}")

        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(15))
        content.add_widget(Label(text="\n".join(lines),
                                font_size=dp(14), halign="left"))
        btn = Button(text="关闭", size_hint=(1, None), height=dp(44),
                    background_color=[.4,.7,.9,1])
        content.add_widget(btn)

        popup = Popup(title=f"📋 {d['ip']} 详情",
                      content=content, size_hint=(.85, .75))
        btn.bind(on_press=popup.dismiss)
        popup.open()


class MainApp(App):
    def build(self):
        self.scanner = DeviceScanner()
        Window.clearcolor = (240/255, 242/255, 245/255, 1)
        return self.create_ui()

    def create_ui(self):
        root = BoxLayout(orientation="vertical", spacing=dp(6), padding=[dp(10), dp(8), dp(10), dp(8)])

        # 标题
        title = Label(
            text="[b]📡 网络设备扫描器[/b]\n[size=12]摄像头 · 交换机 · 路由器[/size]",
            markup=True, font_size=dp(18), size_hint=(1, None), height=dp(55),
            color=[.09, .4, .75, 1])
        root.add_widget(title)

        # 扫描参数
        params = BoxLayout(orientation="vertical", spacing=dp(6), size_hint=(1, None))
        params.bind(minimum_height=params.setter("height"))

        self.ip_input = TextInput(
            text=self.scanner.get_network(),
            multiline=False, font_size=dp(15),
            size_hint=(1, None), height=dp(44),
            background_color=[1,1,1,1], foreground_color=[.13,.13,.13,1],
            hint_text="网段如: 192.168.1.0/24",
            padding=[dp(10), dp(12)])
        params.add_widget(self.ip_input)

        btns = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint=(1, None), height=dp(48))
        self.scan_btn = Button(
            text="▶ 开始扫描", font_size=dp(16), bold=True,
            background_color=[.09, .4, .75, 1], color=[1,1,1,1])
        self.scan_btn.bind(on_press=self.on_scan)
        btns.add_widget(self.scan_btn)

        self.export_btn = Button(
            text="📥 导出", font_size=dp(14),
            background_color=[.2, .2, .2, .05], color=[.09,.4,.75,1])
        self.export_btn.bind(on_press=self.on_export)
        btns.add_widget(self.export_btn)
        params.add_widget(btns)

        # 进度
        self.progress_bar = ProgressBar(max=100, value=0, size_hint=(1, None), height=dp(6))
        params.add_widget(self.progress_bar)
        self.progress_label = Label(text="", font_size=dp(11), color=[.5,.5,.5,1],
                                   size_hint=(1, None), height=dp(14))
        params.add_widget(self.progress_label)
        root.add_widget(params)

        # 筛选 + 统计
        stats = BoxLayout(orientation="horizontal", spacing=dp(12), size_hint=(1, None), height=dp(40))
        self.stat_label = Label(text="设备: 0", bold=True, font_size=dp(14),
                               halign="left", size_hint=(None, 1))
        self.stat_label.bind(texture_size=lambda s, v: setattr(s, "width", v[0] + dp(5)))
        stats.add_widget(self.stat_label)

        self.filter_btn = Button(text="全部 ▼", font_size=dp(12),
                                size_hint=(None, 1), width=dp(80),
                                background_color=[.2,.2,.2,.05])
        self.filter_btn.bind(on_press=self.cycle_filter)
        stats.add_widget(self.filter_btn)
        root.add_widget(stats)

        # 设备列表
        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_y=True)
        self.device_list = BoxLayout(orientation="vertical", spacing=dp(4),
                                     size_hint_y=None, padding=[0, 0, 0, dp(10)])
        self.device_list.bind(minimum_height=self.device_list.setter("height"))

        # 空状态
        self.empty_label = Label(
            text="📡\n\n点击「开始扫描」\n发现网络中的设备",
            font_size=dp(16), color=[.6,.6,.6,1],
            size_hint=(1, None), height=dp(200))
        self.device_list.add_widget(self.empty_label)

        self.scroll.add_widget(self.device_list)
        root.add_widget(self.scroll)

        # 底部状态
        self.status = Label(
            text=f"就绪 | 本机IP: {self.scanner.get_local_ip()}",
            font_size=dp(11), color=[.4,.4,.4,1],
            size_hint=(1, None), height=dp(20))
        root.add_widget(self.status)

        self.all_devices = []
        self.current_filter = "全部"
        self.allowed_filters = ["全部", "摄像头", "交换机", "路由器"]

        return root

    def on_scan(self, instance):
        if self.scanner.running:
            self.scanner.stop()
            self.scan_btn.text = "▶ 开始扫描"
            self.scan_btn.background_color = [.09, .4, .75, 1]
            self.status.text = "扫描已停止"
            return

        network = self.ip_input.text.strip()
        self.all_devices = []
        self.scan_btn.text = "■ 停止"
        self.scan_btn.background_color = [.9, .2, .2, 1]
        self.status.text = "正在扫描..."
        self.progress_bar.value = 0
        self.progress_label.text = ""
        self.device_list.clear_widgets()

        threading.Thread(target=self._scan_thread, args=(network,), daemon=True).start()

    def _scan_thread(self, network):
        self.scanner.scan_network(network, callback=self._device_found)

    def _device_found(self, device, current, total):
        if device:
            self.all_devices.append(device)
        self.progress_bar.value = current * 100 / total if total > 0 else 0
        self.progress_label.text = f"{current}/{total} | 已发现 {len(self.all_devices)} 个"
        self._refresh_list()
        if not self.scanner.running:
            self.scan_btn.text = "▶ 开始扫描"
            self.scan_btn.background_color = [.09, .4, .75, 1]
            self.status.text = f"扫描完成! 共 {len(self.all_devices)} 个设备"
            self.progress_label.text = ""

    def _refresh_list(self):
        self.device_list.clear_widgets()
        filtered = self.all_devices
        if self.current_filter != "全部":
            filtered = [d for d in self.all_devices if self.current_filter in d["type"]]

        if filtered:
            for d in filtered:
                card = DeviceCard(d)
                self.device_list.add_widget(card)
        else:
            self.device_list.add_widget(Label(
                text="📡\n\n没有匹配的设备", font_size=dp(16),
                color=[.6,.6,.6,1], size_hint=(1, None), height=dp(200)))

        # 统计
        cameras = sum(1 for d in self.all_devices if "摄像头" in d["type"])
        switches = sum(1 for d in self.all_devices if "交换机" in d["type"])
        routers = sum(1 for d in self.all_devices if "路由器" in d["type"])
        self.stat_label.text = f"设备: {len(self.all_devices)} 📷{cameras} 🔄{switches} 📡{routers}"

    def cycle_filter(self, instance):
        idx = self.allowed_filters.index(self.current_filter)
        idx = (idx + 1) % len(self.allowed_filters)
        self.current_filter = self.allowed_filters[idx]
        self.filter_btn.text = f"{self.current_filter} ▼"
        self._refresh_list()

    def on_export(self, instance):
        if not self.all_devices:
            self.status.text = "没有数据可导出"
            return

        try:
            if platform == "android":
                from jnius import autoclass
                env = autoclass('android.os.Environment')
                path = env.getExternalStoragePublicDirectory(env.DIRECTORY_DOWNLOADS).getAbsolutePath()
            else:
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                path = os.path.join(desktop, "网络扫描结果")
                os.makedirs(path, exist_ok=True)

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(path, f"scan_result_{ts}.csv")

            with open(filepath, "w", encoding="utf-8-sig") as f:
                f.write("IP地址,MAC地址,厂商,设备类型,品牌,型号,置信度,开放端口\n")
                for d in self.all_devices:
                    ports = "; ".join(str(p) for p in d["ports"])
                    f.write(f"{d['ip']},{d['mac']},{d['vendor']},{d['type']},{d['brand']},{d['model']},{d['confidence']},\"{ports}\"\n")

            self.status.text = f"已导出: {filepath}"

            content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(20))
            content.add_widget(Label(text=f"✅ 导出成功!\n\n{len(self.all_devices)} 个设备\n\n{filepath}",
                                    font_size=dp(15), halign="center"))
            btn = Button(text="好的", size_hint=(1, None), height=dp(44),
                        background_color=[.4,.7,.9,1])
            content.add_widget(btn)
            popup = Popup(title="导出完成", content=content, size_hint=(.8, .45))
            btn.bind(on_press=popup.dismiss)
            popup.open()
        except Exception as e:
            self.status.text = f"导出失败: {e}"


if __name__ == "__main__":
    MainApp().run()
