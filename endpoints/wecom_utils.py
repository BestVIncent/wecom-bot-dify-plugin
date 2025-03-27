import json
import logging
from functools import lru_cache
from typing import Optional

import requests
import xmltodict
from wx_crypt import WXBizMsgCrypt, WxChannel_Wecom

from .models import TextMsgRequest

logger = logging.getLogger(__name__)


@lru_cache(maxsize=50)
def get_wx_cpt(token: str, aes_key: str) -> WXBizMsgCrypt:
    """获取企业微信加解密器

    @param token: 企业微信回调接口的token
    @param aes_key: 企业微信回调接口的aes_key

    @return: 加解密器
    """
    return WXBizMsgCrypt(
        token,
        aes_key,
        "",
        channel=WxChannel_Wecom,
    )


class WecomCrypt:
    def __init__(self, token: str, aes_key: str, webhook_url: str):
        """初始化企业微信加解密器

        @param token: 企业微信回调接口的token
        @param aes_key: 企业微信回调接口的aes_key
        @param webhook_url: 企业微信回调接口的webhook_url
        """
        self.token = token
        self.aes_key = aes_key
        self.webhook_url = webhook_url
        self.wx_cpt = get_wx_cpt(token, aes_key)

    def verify_signature(
        self,
        msg_signature: str,
        timestamp: str,
        nonce: str,
        encrypted_echo_str: str,
    ) -> Optional[str]:
        """验证回调接口的签名

        @param msg_signature: 企业微信回调接口的签名
        @param timestamp: 企业微信回调接口的时间戳
        @param nonce: 企业微信回调接口的随机串
        @param encrypted_echo_str: 企业微信回调接口的加密消息

        @return: 解密后的消息, 如果验证失败, 返回None
        """
        code, decrypted_echo_str = self.wx_cpt.VerifyURL(
            sMsgSignature=msg_signature,
            sTimeStamp=timestamp,
            sNonce=nonce,
            sEchoStr=encrypted_echo_str,
        )
        if code != 0:
            return None
        return decrypted_echo_str

    def decrypt_xml_request_body(
        self,
        msg_signature: str,
        timestamp: str,
        nonce: str,
        body: str,
    ) -> Optional[TextMsgRequest]:
        """解密企业微信回调接口的消息

        @param msg_signature: 企业微信回调接口的签名
        @param timestamp: 企业微信回调接口的时间戳
        @param nonce: 企业微信回调接口的随机串
        @param body: 企业微信回调接口的消息

        @return: 解密后的消息, 如果解密失败, 返回None
        """
        # 解密请求内容
        code, xml_msg = self.wx_cpt.DecryptMsg(body, msg_signature, timestamp, nonce)
        if code != 0:
            return None
        # 解析xml内容
        dict_msg = xmltodict.parse(xml_msg)
        data = dict_msg.get("xml", None)
        if data is not None:
            if data.get("MsgType") == "text":
                return TextMsgRequest(**data)
            else:
                logger.info("wechat bot msg type not supported: %s", data.get("MsgType"))
        return None

    def encrypt_xml_request_body(
        self, xml_data: str, timestamp: str, nonce: str
    ) -> str:
        """加密xml消息

        @param xml_data: xml数据
        @param timestamp: 时间戳
        @param nonce: 随机串

        @return: 加密后的xml数据
        """
        code, encrypt_xml = self.wx_cpt.EncryptMsg(xml_data.encode(), nonce, timestamp)
        if code != 0:
            return None
        return encrypt_xml

    def send_markdown_msg(self, chat_id: str, msg: str) -> bool:
        """向用户发送markdown消息

        @param chat_id: 用户id
        @param msg: 消息内容

        @return: 是否成功
        """
        try:
            requests.post(
                url=self.webhook_url,
                data=json.dumps(
                    {
                        "chatid": chat_id,
                        "msgtype": "markdown",
                        "markdown": {"content": msg},
                    }
                ),
            )
        except Exception as e:
            logger.error("send markdown message error: %s", e)
            return False
        return True
