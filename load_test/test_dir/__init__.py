from hoshino import Service, priv
from hoshino.typing import CQEvent, HoshinoBot

from .test_config import inner_version

sv = Service("更多更多插件管理测试", manage_priv=priv.SUPERUSER, enable_on_default=False, visible=False)


@sv.on_fullmatch('调戏一下')
async def test_once(bot: HoshinoBot, ev: CQEvent):
    await bot.send(ev, f"内部版本：{inner_version}", at_sender=True)
