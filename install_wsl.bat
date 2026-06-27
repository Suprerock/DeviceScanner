@echo off
chcp 65001 >nul
title WSL Ubuntu 离线安装
echo ========================================
echo   WSL Ubuntu 手动安装脚本
echo   网络设备扫描器 APK 打包工具
echo ========================================
echo.
echo 第1步 - 下载 Ubuntu WSL 安装包
echo --------------------------------------------
echo 请手动下载 Ubuntu 22.04 WSL 包:
echo.
echo 方法 A: 用浏览器打开微软商店链接
echo   https://www.microsoft.com/store/productId/9PDXGNCFSCZV
echo   点击"获取"按钮安装
echo.
echo 方法 B: 或者用 winget 命令安装（如果可用）
echo   winget install Ubuntu
echo.
echo --------------------------------------------
pause
cls

echo 第2步 - 安装 Ubuntu 并配置
echo --------------------------------------------
echo 安装完成后：
echo   1. 打开开始菜单，启动 Ubuntu
echo   2. 等待初始化（首次约1-2分钟）
echo   3. 设置用户名和密码
echo   4. 依次执行以下命令安装打包工具:
echo.
echo.
echo ===== 复制下面内容到 Ubuntu 终端执行 =====
echo.
echo sudo apt update
echo sudo apt install -y python3-pip python3-dev git autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
echo pip3 install --user buildozer cython
echo echo 'export PATH=$PATH:~/.local/bin' ^>^> ~/.bashrc
echo source ~/.bashrc
echo.
echo ============================================
echo.
pause
cls

echo 第3步 - 打包 APK
echo --------------------------------------------
echo 安装完工具后，在 Ubuntu 中执行：
echo.
echo cd /mnt/c/Users/赵明磊/AppData/Local/Claude-3p/local-agent-mode-sessions/4ae39506/00000000/local_9cab47df-4db5-4fa9-bc86-5bcf4ca52bf0/outputs/kivy_build/
echo buildozer android debug
echo.
echo 首次打包会下载 Android SDK/NDK（约2GB，需等待10-30分钟）
echo 以后每次打包只需1-2分钟
echo.
echo 打包完成后 APK 在: bin/DeviceScanner-*-debug.apk
echo.
echo --------------------------------------------
echo.
echo 复制 APK 到 Windows 桌面:
echo   cp bin/*.apk /mnt/c/Users/赵明磊/Desktop/
echo.
pause
