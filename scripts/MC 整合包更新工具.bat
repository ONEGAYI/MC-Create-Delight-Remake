@echo off
chcp 65001 >nul
title MC 整合包自动更新工具

echo ======================================================
echo           MC 整合包自动更新/修复工具
echo ======================================================
echo.
echo 说明：
echo 1. 本工具用于连接远程仓库，实现模组自动更新。
echo 2. 如果你本地已经有模组，它不会重复下载（省流量）。
echo 3. 以后每次有更新，双击运行此脚本即可。
echo.

:: --------------------------------------------------------
:: 1. 智能定位目录
:: --------------------------------------------------------
:: 这里的文件夹名要改成你实际的文件夹名
set "REPO_DIR=Create-Delight-Remake"
set "REPO_URL=https://github.com/ONEGAYI/MC-Create-Delight-Remake.git"

:: 检测是否已经在文件夹内
if exist "mods" (
    echo [状态] 脚本似乎已在游戏根目录下，直接开始。
) else (
    if exist "%REPO_DIR%" (
        echo [状态] 发现子目录，正在进入...
        cd "%REPO_DIR%"
    ) else (
        echo [错误] 找不到游戏目录，请把此脚本放在整合包文件夹旁边或里面。
        pause
        exit
    )
)

:: --------------------------------------------------------
:: 2. 判断是“初次安装”还是“日常更新”
:: --------------------------------------------------------
if exist ".git" (
    goto :UPDATE_MODE
) else (
    goto :SETUP_MODE
)

:: --------------------------------------------------------
:: 3. 模式 A: 初次连接 (SETUP_MODE)
:: --------------------------------------------------------
:SETUP_MODE
echo.
echo [模式] 初次连接仓库...
echo ------------------------------------------------------
echo 正在初始化 Git...
git init

:: 【关键配置】
:: 开启自动换行符转换，防止 Windows/Linux 差异导致全量重新下载
git config core.autocrlf true
git config core.safecrlf false
:: 设置较大的缓存，防止大文件报错
git config http.postBuffer 524288000

echo 添加远程地址...
git remote add origin %REPO_URL%

echo.
echo [关键步骤] 正在对比本地文件和远程服务器...
echo 如果你已经有了大部分文件，这一步会很快，只下载差异部分。
echo ------------------------------------------------------

:: 现在的（只下载小于 500KB 的文件内容，既保留了 Git Graph 的功能，又过滤了大 Mod）：
git fetch origin master --depth=1 --filter=blob:limit=500k

echo [关键步骤] 正在强行下载并写入 .gitignore...
:: 解释：git show 直接读取远程分支的特定文件内容，并用 > 写入本地
:: 这样避开了 checkout 的索引检查机制
git show origin/master:.gitignore > .gitignore
echo .gitignore 恢复完成。
echo.

echo.
echo [关键步骤] 重置指针...
:: 这步会让 Git 承认你本地的文件，不会修改它们
git reset --mixed origin/master

echo.
echo [关键步骤] 关联分支...
git branch --set-upstream-to=origin/master master

echo [关键步骤] 恢复所有文件到远程状态...
:: 这一步会将所有本地文件恢复到与远程仓库完全一致的状态
git restore --source=origin/master ./*
echo 文件恢复完成。
echo.

echo 检查状态...
echo.
echo ------------------------------------------------------
echo 状态说明：
echo 1. 此时 .gitignore 应该已经存在了。
echo 2. 如果显示 "modified: xxx"，说明你本地的文件内容和远程不一样。
echo 3. 如果显示 "deleted: xxx"，说明远程有这个文件，但你本地没有。
echo    (如果需要恢复某个缺失的文件，请使用: git restore [文件名])
echo ------------------------------------------------------
echo.
git status
echo.

echo.
echo [成功] 连接完成！现在你的客户端已与远程同步。
goto :END_PROCESS


:: --------------------------------------------------------
:: 4. 模式 B: 日常更新 (UPDATE_MODE)
:: --------------------------------------------------------
:UPDATE_MODE
echo.
echo [模式] 检测更新...
echo ------------------------------------------------------

:: 先获取远程最新状态
git fetch origin master

:: 检查是否有更新
for /f %%i in ('git rev-list HEAD...origin/master --count') do set COUNT=%%i

if "%COUNT%"=="0" (
    echo.
    echo [提示] 当前已经是最新版本，无需更新。
) else (
    echo.
    echo [提示] 发现 %COUNT% 个新改动（新模组或配置）。
    echo 正在拉取更新...
    
    :: 拉取并合并，这会自动下载新 jar，删除旧 jar
    git pull origin master
    
    echo.
    echo [成功] 更新已安装完毕！
)

goto :END_PROCESS

:: --------------------------------------------------------
:: 5. 结束
:: --------------------------------------------------------
:END_PROCESS
echo.
echo ======================================================
echo                 操作完成
echo ======================================================
echo 按任意键退出...
pause >nul
exit