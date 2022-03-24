import os
import re
import sys
import nonebot
import importlib
from types import ModuleType
from apscheduler.jobstores.base import JobLookupError

from nonebot import on_command, scheduler
from hoshino import log, trigger, Service
from hoshino.typing import CommandSession
from hoshino.trigger import PrefixTrigger, SuffixTrigger, KeywordTrigger, RexTrigger

'''
指令：插件列表、加载插件、卸载插件、重载插件、卸载计划任务、加载插件配置、重载插件配置、批量加载插件、批量卸载插件、批量重载插件
on_command、on_natural_language、on_notice、on_request都已在nonebot.plugin.PluginManager.remove_plugin中清理
已支持Service在hoshino.service管理Dict中的清理
已支持ServiceFunc在hoshino.trigger.chain中的清理
已支持scheduled_job在nonebot.scheduler中的清理
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
    await session.aget('module', prompt='请输入需要加载的模块')
    module = session.state['module']
    module_path = 'hoshino.modules.' + module
    if module_path in sys.modules:
        await session.finish('该插件已加载，请使用重载插件指令')
    nonebot.plugin.load_plugin(module_path)
    if module_path in sys.modules:
        logger.info(f'Succeeded to load "{module}"')
        await session.send(f'成功加载{module_path}')
    else:
        logger.warning(f'Failed to load "{module}"')
        await session.send(f'加载失败')


def unload_services(moudle: ModuleType):
    loaded_services = Service.get_loaded_services()
    service_bundle = Service.get_bundles()
    for value in moudle.__dict__.values():
        if isinstance(value, Service):
            sv_name = value.name
            del loaded_services[value.name]
            logger.info(f'Succeeded to unload {value.name} in Services')
            for _bundle in service_bundle.values():
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
    await session.aget('module', prompt='请输入需要卸载的模块')
    module = session.state['module']
    module_path = 'hoshino.modules.' + module
    if module_path not in sys.modules:
        await session.finish(f'该插件未被加载')
    module_obj = sys.modules[module_path]
    unload_services(module_obj)
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
    await session.aget('module', prompt='请输入需要重载的模块')
    module = session.state['module']
    module_path = 'hoshino.modules.' + module
    if module_path not in sys.modules:
        await session.finish('该插件未被加载，请使用加载插件指令')
    module_obj = sys.modules[module_path]
    unload_services(module_obj)
    new_plugin = nonebot.plugin.reload_plugin(module_path)
    if new_plugin is not None:
        logger.info(f'Succeeded to reload "{module}"')
        await session.send(f'成功重载{module_path}')
    else:
        logger.warning(f'Failed to reload "{module}"')
        await session.send(f'重载失败')


@on_command('卸载计划任务', aliases={'scheduled job unload', })
async def unload_plugin(session: CommandSession):
    if session.ctx.get('group_id'):
        await session.finish('请私聊bot')
    if session.ctx['user_id'] not in session.bot.config.SUPERUSERS:
        await session.finish('你不是主人，没有此命令的权限')
    await session.aget('job_id', prompt='请输入需要卸载的计划任务')
    job_id = session.state['job_id']
    try:
        scheduler.remove_job(job_id)
        await session.send(f'成功卸载计划任务{job_id}')
    except JobLookupError as e:
        logger.error(str(e))
        await session.send(f'卸载失败')


@on_command('加载插件配置', aliases={'plug config load', 'plugin config load'})
async def reload_plugin_config(session: CommandSession):
    if session.ctx.get('group_id'):
        await session.finish('请私聊bot')
    if session.ctx['user_id'] not in session.bot.config.SUPERUSERS:
        await session.finish('你不是主人，没有此命令的权限')
    await session.aget('module', prompt='请输入需要加载的插件配置')
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
    await session.aget('module', prompt='请输入需要重载的插件配置')
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


def _load_plugin_directory(directory: str):
    msg = ''
    plugin_dir = os.path.join('hoshino/modules', directory)
    count = set()
    if not os.path.isdir(plugin_dir):
        return '无法找到该文件夹'
    for name in os.listdir(plugin_dir):
        path = os.path.join(plugin_dir, name)
        if os.path.isfile(path) and (name.startswith('_') or not name.endswith('.py')):
            continue
        if os.path.isdir(path) and (name.startswith('_') or not os.path.exists(os.path.join(path, '__init__.py'))):
            continue
        m = re.match(r'([_A-Z0-9a-z]+)(.py)?', name)
        if not m:
            continue
        module_path = f'hoshino.modules.{directory}.{m.group(1)}'
        if module_path in sys.modules:
            logger.info(f'"{name}" is already loaded')
            msg += f'模组{module_path}已被加载，跳过\n'
            continue
        result = nonebot.plugin.load_plugin(module_path)
        if result:
            count.add(result)
        if module_path in sys.modules:
            logger.info(f'Succeeded to load "{name}"')
            msg += f'成功加载{module_path}\n'
        else:
            logger.warning(f'Failed to load "{name}"')
            msg += f'模组{module_path}加载失败\n'
    if (plug_num := len(count)) > 0:
        msg += f'成功加载了{plug_num}个插件\n'
    else:
        msg += f'未找到任何插件\n'
    return msg


@on_command('批量加载插件', aliases={'plug dir load', 'plugin directory load'})
async def load_plugin_directory(session: CommandSession):
    if session.ctx.get('group_id'):
        await session.finish('请私聊bot')
    if session.ctx['user_id'] not in session.bot.config.SUPERUSERS:
        await session.finish('你不是主人，没有此命令的权限')
    await session.aget('directory', prompt='请输入需要加载的文件夹')
    directory = session.state['directory']
    msg = _load_plugin_directory(directory)
    await session.send(msg)


def _unload_plugin_directory(directory: str):
    msg = ''
    directory_path = f'hoshino.modules.{directory}'
    count = 0
    for module_path in list(filter(lambda x: x.startswith(directory_path), sys.modules.keys())):
        module_obj = sys.modules[module_path]
        unload_services(module_obj)
        if nonebot.plugin.PluginManager.remove_plugin(module_path):
            logger.info(f'Succeeded to unload "{module_path.split(".")[-1]}"')
            msg += f'插件{module_path}卸载成功\n'
        else:
            logger.info(f'Succeeded to unload "{module_path}"')
            msg += f'模组{module_path}卸载成功\n'
        count += 1
        sys.modules.pop(module_path)
    if count > 0:
        msg += f'成功卸载了{count}个插件/模组\n'
    else:
        msg += f'未找到任何插件\n'
    return msg


@on_command('批量卸载插件', aliases={'plug dir unload', 'plugin directory unload'})
async def unload_plugin_directory(session: CommandSession):
    if session.ctx.get('group_id'):
        await session.finish('请私聊bot')
    if session.ctx['user_id'] not in session.bot.config.SUPERUSERS:
        await session.finish('你不是主人，没有此命令的权限')
    await session.aget('directory', prompt='请输入需要卸载的文件夹')
    directory = session.state['directory']
    msg = _unload_plugin_directory(directory)
    await session.send(msg)


@on_command('批量重载插件', aliases={'plug dir reload', 'plugin directory reload'})
async def reload_plugin_directory(session: CommandSession):
    if session.ctx.get('group_id'):
        await session.finish('请私聊bot')
    if session.ctx['user_id'] not in session.bot.config.SUPERUSERS:
        await session.finish('你不是主人，没有此命令的权限')
    await session.aget('directory', prompt='请输入需要重载的文件夹')
    directory = session.state['directory']
    msg = _unload_plugin_directory(directory)
    msg += _load_plugin_directory(directory)
    await session.send(msg)
