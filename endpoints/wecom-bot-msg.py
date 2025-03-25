import logging
import threading
from typing import Mapping

from dify_plugin import Endpoint
from werkzeug import Request, Response

from .models import TextMsgRequest
from .wecom_utils import WecomCrypt

logger = logging.getLogger(__name__)


class WecomBotMsgEndpoint(Endpoint):
    def _invoke(self, r: Request, values: Mapping, settings: Mapping) -> Response:
        """
        企业微信机器人消息回调接口, 接受企业微信机器人消息, 并调用Dify工作流处理
        """

        raw_body = r.get_data()
        wx_crypt = WecomCrypt(
            settings["token"], settings["aes_key"], settings["webhook_url"]
        )
        decrypted_body = wx_crypt.decrypt_xml_request_body(
            r.args.get("msg_signature"),
            r.args.get("timestamp"),
            r.args.get("nonce"),
            raw_body,
        )
        if not decrypted_body:
            logger.info("decrypt xml request body failed")
            return Response(status=403)

        if decrypted_body.msgtype == "text":

            # 这里使用线程来调用工作流并发送消息，避免阻塞主线程
            # 企微回复消息超时
            threading.Thread(
                target=self.invoke_workflow_and_send,
                args=(settings, wx_crypt, decrypted_body),
            ).start()

            return Response(
                status=200,
                content_type="plain/text",
            )
        else:
            logger.info("unsupported msgtype: %s", decrypted_body.msgtype)
        return Response(status=200, content_type="plain/text")

    def invoke_workflow_and_send(
        self,
        settings: Mapping,
        wx_crypt: WecomCrypt,
        decrypted_body: TextMsgRequest,
    ):
        """
        调用Dify工作流并发送消息

        :param settings: 配置
        :param wx_crypt: 加解密工具
        :param decrypted_body: 解密后的消息
        """
        result = self.session.app.workflow.invoke(
            app_id=settings["static_app_id"]["app_id"],
            inputs={
                settings["workflow_text_input_field"]: decrypted_body.text.content,
                "metadata": decrypted_body.model_dump_json(),  # 将整个请求体作为元数据, 方便后续使用
            },
            response_mode="blocking",
        )

        text_output = result["data"]["outputs"][settings["workflow_text_output_field"]]
        wx_crypt.send_markdown_msg(decrypted_body.chatid, text_output)
