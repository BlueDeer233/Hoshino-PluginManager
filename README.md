# Hoshino-PluginManager

适用于hoshinobot的插件管理插件（稍微删改一下就能支持nonebot了）  
仅支持`nonebot 1.8.x、1.9.x`，不支持`nonebot2`（已提交issue，但是作者认为冷重载更合适）  
指令：插件列表、加载插件、卸载插件、重载插件、卸载计划任务、加载插件配置、重载插件配置、批量加载插件、批量卸载插件、批量重载插件  
`on_command`、`on_natural_language`、`on_notice`、`on_request`都已在`nonebot.plugin.PluginManager.remove_plugin`中清理

* 已支持`Service`在`hoshino.service`管理Dict中的清理  
* 已支持`ServiceFunc`在`hoshino.trigger.chain`中的清理  
* 已支持`scheduled_job`在`nonebot.scheduler`中的清理（需要指定任务id，见指令帮助）

**对于存在scheduled_job的插件必须在重载、卸载插件前卸载所包含的计划任务**  
**正如nonebot2作者所言，该插件并不能完全卸载/重载插件，可能包含许多bugs，请慎用**  
**只推荐在开发插件时使用本插件，不推荐在release阶段热重载**  
欢迎issue、fork、pull request

项目地址：[Hoshino-PluginManager](https://github.com/BlueDeer233/Hoshino-PluginManager)

## 使用方法

1、clone本项目在任意位置 `git clone https://github.com/BlueDeer233/Hoshino-PluginManager.git`  
2、将 `pluginManager` 文件夹放入HoshinoBot目录 `hoshino.modules` 下  
(optional) 将 `load_test` 文件夹放入HoshinoBot目录 `hoshino.modules` 下（用于测试）  
(optional) 将 `load_test.py` 文件放入HoshinoBot目录 `hoshino.config` 下（用于测试）  
3、在 `config/__bot__.py` 模块列表中添加 `pluginManager`

## 指令

|   命令    | 功能                                                   |
|:-------:|:-----------------------------------------------------|
|  插件列表   | 输出所有已加载插件（强烈建议初次使用该插件的用户朋友先运行一下这个指令）                 |
|  加载插件   | 根据引导加载插件（只能操作单个文件，必须精确到module文件夹下的某个py文件，不需要输.py）    |
|  卸载插件   | 根据引导卸载插件（要求同上）                                       |
|  重载插件   | 根据引导重载插件（要求同上）                                       |
| *卸载计划任务 | 根据引导卸载计划任务（需要输入scheduled_job的id）                     |
| *加载插件配置 | 根据引导加载`hoshino.config`目录下的配置文件（不需要输.py）              |
| *重载插件配置 | 根据引导重载`hoshino.config`目录下的配置文件（不需要输.py）              |
| 批量加载插件  | 根据引导批量加载`hoshino.modules`文件夹下的文件夹（与__bot__.py逻辑保持一致） |
| 批量卸载插件  | 根据引导批量卸载`hoshino.modules`文件夹下的文件夹（卸载所有文件夹下的文件）       |
| 批量重载插件  | 根据引导批量重载`hoshino.modules`文件夹下的文件夹（逻辑见上两条）            |

*注意：配置文件中变量的导入必须在函数内部（详见[test.py](load_test/test.py)）  
*注意：在生成计划任务时必须指定id，否则无法卸载（详见[test.py](load_test/test.py)）  
*注意：在所有重载操作前应先卸载插件内的计划任务，除非添加`replace_existing=True`（详见[test.py](load_test/test.py)）

## 更新说明

**2020-03-24**

1、初次更新  
2、更新卸载计划任务  
3、批量操作

## TODO

1、scheduled_job更优雅的卸载  
2、前端开发？（前端苦手求救！）
