import logging
from typing import Mapping

from dify_plugin import Endpoint
from werkzeug import Request, Response

from .wecom_utils import WecomCrypt

logger = logging.getLogger(__name__)


class WecomBotVerifyEndpoint(Endpoint):
    def _invoke(self, r: Request, values: Mapping, settings: Mapping) -> Response:
        """
        企业微信验证接口
        """
        msg_signature = r.args.get("msg_signature")
        timestamp = r.args.get("timestamp")
        nonce = r.args.get("nonce")
        echostr = r.args.get("echostr")
        if not msg_signature or not timestamp or not nonce or not echostr:
            return Response(status=400)

        msg = ""
        wx_crypt = WecomCrypt(
            settings["token"], settings["aes_key"], settings["webhook_url"]
        )

        msg = wx_crypt.verify_signature(
            msg_signature,
            timestamp,
            nonce,
            echostr,
        )
        if not msg:
            logger.info("verify signature failed")
            return Response(status=403)

        return Response(msg, status=200, content_type="plain/text")
