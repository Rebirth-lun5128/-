from pydantic import BaseModel


class PayParamsOut(BaseModel):
    """返回给小程序 wx.requestPayment 的参数"""
    appId: str
    timeStamp: str
    nonceStr: str
    package: str
    signType: str = "RSA"
    paySign: str
    isMock: bool = False


class RefundIn(BaseModel):
    reason: str = ""
