from typing import List, Optional

import xmltodict
from pydantic import BaseModel, Field


class TextContent(BaseModel):
    content: str = Field(alias="Content")


class ImageContent(BaseModel):
    image_url: str


class FromWho(BaseModel):
    userid: str = Field(alias="UserId")
    name: str = Field(alias="Name")
    alias: str = Field(alias="Alias")


class Action(BaseModel):
    name: str = Field(alias="Name")
    text: str = Field(alias="Text")
    type: str = Field(alias="Type")
    value: str = Field(alias="Value")
    replace_text: str = Field(alias="ReplaceText")
    border_color: str = Field(alias="BorderColor")
    text_color: str = Field(alias="TextColor")


class Attachment(BaseModel):
    callback_id: str = Field(alias="CallbackId")
    actions: List[Action] = Field(default=[], alias="Actions")


class MarkdownContent(BaseModel):
    content: str = Field(alias="Content")
    # at_short_name: bool = Field(default=False, alias="AtShortName")
    attachment: List[Attachment] = Field(default=[], alias="Attachment")


class TextMsgRequest(BaseModel):
    """企业微信机器人回调消息，作为请求接收"""

    webhook_url: str = Field(alias="WebhookUrl")
    msgid: str = Field(alias="MsgId")
    chatid: str = Field(alias="ChatId")
    postid: Optional[str] = Field(default=None, alias="PostId")
    chattype: str = Field(alias="ChatType")
    from_who: FromWho = Field(alias="From")
    get_chat_info_url: str = Field(alias="GetChatInfoUrl")
    msgtype: str = Field(alias="MsgType")
    text: TextContent = Field(alias="Text")


class MarkdownMsgResponse(BaseModel):
    """企业微信机器人回调消息，作为响应发送"""

    msgtype: str = Field(default="markdown", alias="MsgType")
    markdown: MarkdownContent = Field(alias="Markdown")
    visible_to_user: str = Field(default="", alias="VisibleToUser")

    def to_xml(self) -> str:
        """将响应消息转换为xml格式"""
        dict = self.model_dump(by_alias=True)
        xml_data = xmltodict.unparse(
            {"xml": dict}, pretty=False, encoding="utf-8", full_document=False
        )
        return xml_data


class MarkdownSendMsg(BaseModel):
    """企业微信机器人主动发送消息"""

    chatid: str = Field(alias="ChatId")
    post_id: str = Field(default=None, alias="PostId")
    msgtype: str = Field(alias="MsgType")
    visible_to_user: str = Field(alias="VisibleToUser")
    markdown: MarkdownContent = Field(alias="Markdown")
    from_who: FromWho = Field(alias="From")

    def to_xml(self) -> str:
        """将响应消息转换为xml格式"""
        dict = self.model_dump(by_alias=True)
        xml_data = xmltodict.unparse({"xml": dict}, pretty=False, encoding="utf-8")
        return xml_data
