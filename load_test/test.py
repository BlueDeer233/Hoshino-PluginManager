from hoshino import log, Service, priv
from hoshino.typing import CQEvent, HoshinoBot

logger = log.new_logger('插件管理测试', False)

sv = Service("插件管理测试", manage_priv=priv.SUPERUSER, enable_on_default=False, visible=False)


@sv.on_fullmatch(['loadtest', 'LoadTest'])
async def load_test_help(bot: HoshinoBot, ev: CQEvent):
    from hoshino.config.load_test import version
    await bot.send(ev, f"配置文件版本：{version}", at_sender=True)


@sv.on_rex(r'.*测试一下.*')
async def test_once(bot: HoshinoBot, ev: CQEvent):
    from hoshino.config.load_test import version
    await bot.send(ev, f"配置文件版本：{version}", at_sender=True)


@sv.scheduled_job('cron', id='loadtest', second='*/5', replace_existing=True)
async def test_scheduled_job():
    logger.info('我被调用了')
