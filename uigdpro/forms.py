from django import forms
from PIL import Image

class GenerateForm(forms.Form):
    # 平台
    platform = forms.ChoiceField(
        choices=[
            ('windows', 'Windows 64位'),
            ('windows-x86', 'Windows 32位'),
            ('linux', 'Linux'),
            ('android', 'Android'),
            ('macos', 'macOS')
        ],
        initial='windows',
        label="目标平台"
    )
    
    version = forms.ChoiceField(
        choices=[
            ('master', '开发版（每夜构建）'),
            ('1.4.4', '1.4.4'),
            ('1.4.3', '1.4.3'),
            ('1.4.2', '1.4.2'),
            ('1.4.1', '1.4.1'),
            ('1.4.0', '1.4.0'),
            ('1.3.9', '1.3.9'),
            ('1.3.8', '1.3.8'),
            ('1.3.7', '1.3.7'),
            ('1.3.6', '1.3.6'),
            ('1.3.5', '1.3.5'),
            ('1.3.4', '1.3.4'),
            ('1.3.3', '1.3.3')
        ],
        initial='1.4.4',
        label="版本"
    )
    help_text = "“开发版”是包含最新功能的每夜构建版本，但可能稳定性较低"

    delayFix = forms.BooleanField(initial=True, required=False, label="启用延迟修复")

    # 基本设置
    exename = forms.CharField(label="EXE 文件名称", required=True)
    appname = forms.CharField(label="自定义应用名称", required=False)
    
    direction = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=[
            ('incoming', '仅允许传入连接'),
            ('outgoing', '仅允许传出连接'),
            ('both', '双向连接')
        ],
        initial='both',
        label="连接方向"
    )
    
    installation = forms.ChoiceField(
        label="禁用安装功能",
        choices=[
            ('installationY', '否，启用安装'),
            ('installationN', '是，禁用安装')
        ],
        initial='installationY'
    )
    
    settings = forms.ChoiceField(
        label="禁用设置界面",
        choices=[
            ('settingsY', '否，启用设置'),
            ('settingsN', '是，禁用设置')
        ],
        initial='settingsY'
    )

    # 自定义服务器
    serverIP = forms.CharField(label="主机地址（Host）", required=False)
    apiServer = forms.CharField(label="API 服务器地址", required=False)
    key = forms.CharField(label="加密密钥（Key）", required=False)
    urlLink = forms.CharField(label="自定义链接跳转地址", required=False)
    downloadLink = forms.CharField(label="自定义新版本下载地址", required=False)
    compname = forms.CharField(label="公司名称", required=False)

    # 视觉主题
    iconfile = forms.FileField(
        label="自定义应用图标（PNG 格式）",
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/png'})
    )
    logofile = forms.FileField(
        label="自定义应用 Logo（PNG 格式）",
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/png'})
    )
    custom_dart_file = forms.FileField(
        label="上传模板",
        required=False,
        widget=forms.FileInput(attrs={'accept': '.dart'})
    )
    custom_dart_path = forms.CharField(
        label="替换模板",
        required=False,
        help_text=""
    )
    iconbase64 = forms.CharField(required=False)
    logobase64 = forms.CharField(required=False)
    
    theme = forms.ChoiceField(
        choices=[
            ('light', '浅色主题'),
            ('dark', '深色主题'),
            ('system', '跟随系统')
        ],
        initial='system',
        label="界面主题"
    )
    
    themeDorO = forms.ChoiceField(
        choices=[
            ('default', '默认设置'),
            ('override', '强制覆盖')
        ],
        initial='default',
        label="主题策略"
    )

    # 安全设置
    passApproveMode = forms.ChoiceField(
        choices=[
            ('password', '通过密码接受会话'),
            ('click', '通过点击接受会话'),
            ('password-click', '两者均可')
        ],
        initial='password-click',
        label="会话验证方式"
    )
    
    permanentPassword = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        label="永久密码"
    )
    
    denyLan = forms.BooleanField(initial=False, required=False, label="禁止局域网发现")
    enableDirectIP = forms.BooleanField(initial=False, required=False, label="启用直连 IP")
    autoClose = forms.BooleanField(initial=True, required=False, label="会话结束后自动关闭")

    # 权限控制
    permissionsDorO = forms.ChoiceField(
        choices=[
            ('default', '默认权限'),
            ('override', '强制覆盖权限')
        ],
        initial='default',
        label="权限策略"
    )
    
    permissionsType = forms.ChoiceField(
        choices=[
            ('custom', '自定义权限'),
            ('full', '完全控制'),
            ('view', '仅屏幕共享')
        ],
        initial='custom',
        label="访问模式"
    )
    
    enableKeyboard = forms.BooleanField(initial=True, required=False, label="启用键盘控制")
    enableClipboard = forms.BooleanField(initial=True, required=False, label="启用剪贴板同步")
    enableFileTransfer = forms.BooleanField(initial=True, required=False, label="启用文件传输")
    enableAudio = forms.BooleanField(initial=False, required=False, label="启用音频传输")
    enableTCP = forms.BooleanField(initial=True, required=False, label="启用 TCP 隧道")
    enableRemoteRestart = forms.BooleanField(initial=True, required=False, label="启用远程重启")
    enableRecording = forms.BooleanField(initial=True, required=False, label="启用会话录制")
    enableBlockingInput = forms.BooleanField(initial=True, required=False, label="启用输入锁定")
    enableRemoteModi = forms.BooleanField(initial=False, required=False, label="允许远程修改配置")
    hidecm = forms.BooleanField(initial=False, required=False, label="隐藏连接管理器")
    enablePrinter = forms.BooleanField(initial=False, required=False, label="启用远程打印")
    enableCamera = forms.BooleanField(initial=True, required=False, label="启用摄像头访问")
    enableTerminal = forms.BooleanField(initial=True, required=False, label="启用终端访问")

    # 其他选项
    removeWallpaper = forms.BooleanField(initial=False, required=False, label="移除桌面壁纸")
    
    defaultManual = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label="默认设置（每行格式：key=value）"
    )
    
    overrideManual = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label="强制覆盖设置（每行格式：key=value）"
    )

    # 自定义增强功能
    cycleMonitor = forms.BooleanField(initial=False, required=False, label="会话顶部添加显示器切换按钮")
    xOffline = forms.BooleanField(initial=True, required=False, label="在地址簿添加离线标记")
    removeNewVersionNotif = forms.BooleanField(initial=False, required=False, label="移除安装更新通知")
    hidePassword = forms.BooleanField(initial=False,required=False,label="移除密码显示(仅允许传入连接模式下勾选)")
    hideMenuBar = forms.BooleanField(initial=False,required=False,label="移除三点菜单(仅允许传入连接模式下勾选)")
    removeTopNotice = forms.BooleanField(initial=True,required=False,label="移除顶部温馨提示（固定密码默认会显示）")
    password_security_length=forms.BooleanField(initial=False,required=False,label="修改临时密码的长度")
    def clean_iconfile(self):
        print("checking icon")
        image = self.cleaned_data['iconfile']
        if image:
            try:
                img = Image.open(image)
                if img.format != 'PNG':
                    raise forms.ValidationError("仅允许 PNG 图像。")
                width, height = img.size
                if width != height:
                    raise forms.ValidationError("应用图标必须为正方形。")
                return image
            except OSError:
                raise forms.ValidationError("无效的图标文件。")
            except Exception as e:
                raise forms.ValidationError(f"处理图标时出错：{e}")
