import sys
import nonebot
import importlib
from types import ModuleType
from nonebot import on_command
from hoshino import log, trigger, Service
from hoshino.typing import CommandSession
from hoshino.service import _loaded_services, _service_bundle
from hoshino.trigger import PrefixTrigger, SuffixTrigger, KeywordTrigger, RexTrigger

'''
适用于hoshinobot的插件管理插件（稍微删改一下就能支持nonebot了）
仅支持nonebot 1.8.x、1.9.x，不支持nonebot2（已提交issue，但是作者认为冷重载更合适）
指令：插件列表、加载插件、卸载插件、重载插件、重载插件配置
on_command、on_natural_language、on_notice、on_request都已在nonebot.plugin.PluginManager.remove_plugin中清理
已支持Service在hoshino.service管理Dict中的清理
已支持ServiceFunc在hoshino.trigger.chain中的清理
尚未支持scheduled_job在nonebot.scheduler中的清理
简而言之对于存在scheduled_job的插件现无法做到卸载与热重载
正如nonebot2作者所言，该插件并不能完全卸载/重载插件，可能包含许多bugs，请慎用
'''


logger = log.new_logger('插件管理', False)


@on_command('插件列表', aliases={'plug list', 'plugin list'})
async def plugin_list(session: CommandSession):
    if session.ctx.get('group_id'):
        await session.finish('请私聊bot')
    if session.ctx['user_id'] not in session.bot.config.SUPERUSERS:
        await session.finish('你不是主人，没有此命令的权限')
    plugins = nonebot.get_loaded_plugins()
    msg = ''
    for i, plug in enumerate(plugins):
        msg += f'plug{i:02d}: {plug.module.__name__.replace("hoshino.modules.", "")}\n'
    await session.send(msg)


@on_command('加载插件', aliases={'plug load', 'plugin load'})
async def load_plugin(session: CommandSession):
    if session.ctx.get('group_id'):
        await session.finish('请私聊bot')
    if session.ctx['user_id'] not in session.bot.config.SUPERUSERS:
        await session.finish('你不是主人，没有此命令的权限')
    await session.aget('module', prompt='请选择需要加载的模块')
    module = session.state['module']
    module_path = 'hoshino.modules.' + module
    plugin_names = [p.module.__name__ for p in nonebot.get_loaded_plugins()]
    if module_path in plugin_names:
        await session.finish('该插件已加载，请使用重载插件指令')
    # try:
    #     importlib.import_module('hoshino.config.' + module)
    #     await session.send(f'Succeeded to load config of "{module}"')
    # except ModuleNotFoundError:
    #     await session.send(f'Not found config of "{module}"')
    nonebot.plugin.load_plugin(module_path)
    plugin_names = [p.module.__name__ for p in nonebot.get_loaded_plugins()]
    if module_path in plugin_names:
        logger.info(f'Succeeded to load "{module}"')
        await session.send(f'成功加载{module_path}')
    else:
        logger.warning(f'Failed to load "{module}"')
        await session.send(f'加载失败')


def unload_services(moudle: ModuleType):
    for value in moudle.__dict__.values():
        if isinstance(value, Service):
            sv_name = value.name
            del _loaded_services[value.name]
            logger.info(f'Succeeded to unload {value.name} in Services')
            for _bundle in _service_bundle.values():
                for i, sv in enumerate(_bundle):
                    if sv.name == sv_name:
                        _bundle.pop(i)
                        logger.info(f'Succeeded to unload {value.name} in Service Bundles')
            for t in trigger.chain:
                if isinstance(t, (PrefixTrigger, SuffixTrigger)):
                    t_dict = t.trie
                elif isinstance(t, KeywordTrigger):
                    t_dict = t.allkw
                elif isinstance(t, RexTrigger):
                    t_dict = t.allrex
                else:
                    continue
                fix_delete = []
                for fix, sfs in t_dict.items():
                    for i, sf in enumerate(sfs):
                        if sf.sv.name == sv_name:
                            t_dict[fix].pop(i)
                            logger.info(f'Succeeded to unload {fix}:{sf.__name__}@{sf.sv.name} in {type(t).__name__}.dict')
                        if len(sfs) == 0:
                            fix_delete.append(fix)
                for fix in fix_delete:
                    t_dict.pop(fix)
                    logger.info(f'Succeeded to delete {fix} in {type(t).__name__}.dict')


@on_command('卸载插件', aliases={'plug unload', 'plugin unload'})
async def unload_plugin(session: CommandSession):
    if session.ctx.get('group_id'):
        await session.finish('请私聊bot')
    if session.ctx['user_id'] not in session.bot.config.SUPERUSERS:
        await session.finish('你不是主人，没有此命令的权限')
    await session.aget('module', prompt='请选择需要加载的模块')
    module = session.state['module']
    module_path = 'hoshino.modules.' + module
    plugin_names = [p.module.__name__ for p in nonebot.get_loaded_plugins()]
    if module_path not in plugin_names:
        await session.finish(f'该插件未被加载')
    moudle_obj = [p.module for p in nonebot.get_loaded_plugins() if p.module.__name__ == module_path][0]
    unload_services(moudle_obj)
    if nonebot.plugin.PluginManager.remove_plugin(module_path):
        sys.modules.pop(module_path)
        logger.info(f'Succeeded to unload "{module}"')
        await session.finish(f'卸载成功')
    else:
        logger.warning(f'Failed to unload "{module}"')
        await session.finish(f'卸载失败')


@on_command('重载插件', aliases={'plug reload', 'plugin reload'})
async def reload_plugin(session: CommandSession):
    if session.ctx.get('group_id'):
        await session.finish('请私聊bot')
    if session.ctx['user_id'] not in session.bot.config.SUPERUSERS:
        await session.finish('你不是主人，没有此命令的权限')
    await session.aget('module', prompt='请选择需要加载的模块')
    module = session.state['module']
    module_path = 'hoshino.modules.' + module
    plugin_names = [p.module.__name__ for p in nonebot.get_loaded_plugins()]
    if module_path not in plugin_names:
        await session.finish('该插件未被加载，请使用加载插件指令')
    moudle_obj = [p.module for p in nonebot.get_loaded_plugins() if p.module.__name__ == module_path][0]
    unload_services(moudle_obj)
    new_plugin = nonebot.plugin.reload_plugin(module_path)
    if new_plugin is not None:
        logger.info(f'Succeeded to reload "{module}"')
        await session.send(f'成功重载{module_path}')
    else:
        logger.warning(f'Failed to reload "{module}"')
        await session.send(f'重载失败')


@on_command('加载插件配置', aliases={'plug config load', 'plugin config load'})
async def reload_plugin_config(session: CommandSession):
    if session.ctx.get('group_id'):
        await session.finish('请私聊bot')
    if session.ctx['user_id'] not in session.bot.config.SUPERUSERS:
        await session.finish('你不是主人，没有此命令的权限')
    await session.aget('module', prompt='请选择需要加载的模块')
    module = session.state['module']
    config_path = 'hoshino.config.' + module
    if config_path in sys.modules:
        await session.finish(f'该配置文件已加载')
    try:
        importlib.import_module(config_path)
        logger.info(f'Succeeded to load config of "{module}"')
        await session.send(f'成功加载{config_path}')
    except ModuleNotFoundError:
        logger.warning(f'Not found config of "{module}"')
        await session.send(f'无法找到该配置文件')


@on_command('重载插件配置', aliases={'plug config reload', 'plugin config reload'})
async def reload_plugin_config(session: CommandSession):
    if session.ctx.get('group_id'):
        await session.finish('请私聊bot')
    if session.ctx['user_id'] not in session.bot.config.SUPERUSERS:
        await session.finish('你不是主人，没有此命令的权限')
    await session.aget('module', prompt='请选择需要加载的模块')
    module = session.state['module']
    config_path = 'hoshino.config.' + module
    try:
        sys.modules.pop(config_path)
        importlib.import_module(config_path)
        logger.info(f'Succeeded to reload config of "{module}"')
        await session.send(f'成功重载{config_path}')
    except KeyError:
        await session.send(f'该配置文件未加载')
    except ModuleNotFoundError:
        logger.warning(f'Not found config of "{module}"')
        await session.send(f'无法找到该配置文件')
