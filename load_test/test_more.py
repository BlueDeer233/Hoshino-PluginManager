from hoshino import Service, priv
from hoshino.typing import CQEvent, HoshinoBot

sv = Service("更多插件管理测试", manage_priv=priv.SUPERUSER, enable_on_default=False, visible=False)


@sv.on_fullmatch('调试一下')
async def test_once(bot: HoshinoBot, ev: CQEvent):
    from hoshino.config.load_test import version
    await bot.send(ev, f"配置文件版本：{version}", at_sender=True)
