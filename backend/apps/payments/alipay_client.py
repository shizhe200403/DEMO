"""
支付宝 SDK 封装。
使用 alipay-sdk-python3 库（pip install alipay-sdk-python3）。
所有密钥均从 Django settings 读取，settings 从环境变量读取。

配置项（在 .env.production 中填写）：
    ALIPAY_APP_ID        — 支付宝开放平台 APPID
    ALIPAY_PRIVATE_KEY   — 应用私钥（PKCS8，不含 header/footer，可多行或单行）
    ALIPAY_PUBLIC_KEY    — 支付宝公钥（不含 header/footer，用于验签）
    ALIPAY_SANDBOX       — true → 沙箱; false（默认）→ 正式环境
"""
import textwrap

from django.conf import settings


def _wrap_key(raw: str, key_type: str) -> str:
    """将裸密钥字符串包装成 PEM 格式。"""
    raw = raw.strip().replace(" ", "").replace("\n", "")
    header = f"-----BEGIN {key_type}-----"
    footer = f"-----END {key_type}-----"
    # 每 64 字符换行
    body = "\n".join(textwrap.wrap(raw, 64))
    return f"{header}\n{body}\n{footer}"


def get_alipay_client():
    """
    返回配置好的 AliPay 实例。
    若未配置 ALIPAY_APP_ID 则抛出 RuntimeError（防止误调用）。
    """
    from alipay import AliPay, AliPayConfig

    app_id = getattr(settings, "ALIPAY_APP_ID", "")
    if not app_id:
        raise RuntimeError("支付宝未配置：请在环境变量中设置 ALIPAY_APP_ID 等参数。")

    private_key_raw = getattr(settings, "ALIPAY_PRIVATE_KEY", "")
    public_key_raw  = getattr(settings, "ALIPAY_PUBLIC_KEY", "")

    app_private_key_string  = _wrap_key(private_key_raw,  "RSA PRIVATE KEY")
    alipay_public_key_string = _wrap_key(public_key_raw, "PUBLIC KEY")

    sandbox = getattr(settings, "ALIPAY_SANDBOX", False)

    client = AliPay(
        appid=app_id,
        app_notify_url=None,          # 单次支付在 create_order_url 中传入
        app_private_key_string=app_private_key_string,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",
        debug=sandbox,
        verbose=False,
        config=AliPayConfig(timeout=15),
    )
    return client, sandbox
