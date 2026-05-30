"""通用工具函数"""


def mask_phone(phone: str) -> str:
    """手机号脱敏：138****0000"""
    if not phone or len(phone) < 7:
        return phone or ""
    return phone[:3] + "****" + phone[-4:]


def mask_phone_for_role(phone: str, viewer_is_owner: bool = False) -> str:
    """
    根据查看者角色决定是否脱敏。
    viewer_is_owner=True 时返回完整号码，否则返回脱敏号码。
    """
    if viewer_is_owner:
        return phone
    return mask_phone(phone)
