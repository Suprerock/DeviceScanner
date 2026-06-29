[app]

# 应用名称
title = 网络设备扫描器
package.name = DeviceScanner
package.domain = com.devicescanner

# 版本
version.code = 1
version = 2.0.0

# Python 需求（Kivy + 标准库）
requirements = python3,kivy,hostpython3,plyer

# Android 最低版本
android.api = 34
android.minapi = 26
android.ndk = 28c
android.sdk = 34

# 权限
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# 不压缩 .so 文件（加快启动）
android.no-glib = 1
android.no-bytecode = 0

# 图标（可选，建议用 512x512 PNG）
# android.icon = icon.png

# 屏幕方向
orientation = portrait

# 启动时全屏
fullscreen = 0

# 是否隐藏日志窗口（发布时设为1）
android.wakelock = 1

# 允许 cleartext HTTP（局域网扫描需要）
android.allow_cleartext = 1

# 打包目标
source.dir = .
source.include_exts = py,png,jpg,jpeg,gif,ttf,txt

# 日志级别
log_level = 2

# 仓库镜像（加速下载，中国大陆推荐）
p4a.branch = develop
p4a.bootstrap = sdl2
android.accept_sdk_license = True



[buildozer]

# 日志级别
log_level = 2

# 编译时警告
warn_on_root = 1
