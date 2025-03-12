'''
Description: 
Version: 2.0
Autor: miaoguoqiang
Date: 2025-02-24 20:02:00
LastEditors: miaoguoqiang
LastEditTime: 2025-03-12 21:25:30
'''
import json
import os
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import Entity
from homeassistant.components.persistent_notification import async_create
from .const import DOMAIN
from .device import Device
from .api import fetch_devices,TokenExpiredError

PLATFORMS = [
    "cover",
    "button",
    "light",
]

_LOGGER = logging.getLogger(__name__)


async def notify_user(hass: HomeAssistant):
    """发出通知，提示用户令牌过期需要重新配置。"""
    try:
        # 检查 hass 对象和其他参数
        if hass is None:
            raise ValueError("hass 对象无效")
        notification = await async_create(
            hass,
            "您的令牌已过期，请在集成页面重新配置。",
            title="令牌过期",
            notification_id="token_expiry_notification"  # 可选，方便后续管理通知
        )
        
        # 可选择添加日志记录以确认通知创建是否成功
        if notification is None:
            _LOGGER.warning("未能创建通知，返回 None")
        else:
            _LOGGER.info("通知已成功创建")
            
    except Exception as e:
        _LOGGER.error(f"创建通知时出错: {e}")
    
async def async_setup(hass: HomeAssistant, config:dict) -> bool:
    """Set up the AnxinJia Control component."""
    # 注册配置流
    # hass.config_entries.HANDLERS[DOMAIN] = AnxinJiaControlConfigFlow
    # 注册重新加载功能
    #async def reload_entry(entry: ConfigEntry):
    #    """重新加载集成配置。"""
    #    await hass.config_entries.async_reload(entry.entry_id)

    hass.data.setdefault(DOMAIN, {})

    # 将重新加载函数存储在 hass.data 中，以便在后续调用
    hass.data[DOMAIN] = {
        #"reload_entry": reload_entry,
        "addressId": None
        # 可存储其他数据
    }
    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    try:
        devices_data = await fetch_devices(hass, config_entry)
    except TokenExpiredError:
        # 处理令牌过期的情况
        _LOGGER.warning("Token expired. Prompting user to reauthorize.")
        # 设备拉取失败，发出通知
        await notify_user(hass)
        return False

    hass.data[DOMAIN].setdefault('devices', {})
    # 初始化当前配置条目的设备列表
    hass.data[DOMAIN]['devices'][config_entry.entry_id] = []
    
    config_entry.async_on_unload(config_entry.add_update_listener(async_reload_entry))

    if not devices_data or not isinstance(devices_data, list):
        _LOGGER.warning("没有获取到设备信息")
        return False
    
    # 获取设备注册表实例
    device_registry = dr.async_get(hass)  # 这里只需要传递 hass 实例

    # 注册设备
    for device_info in devices_data:
        device = Device(device_info)
        
        # 创建或获取设备注册表
        device_entry = device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            identifiers={(DOMAIN, device.eq_number)},
            name= f"{device.physics_name}/{device.eq_name}",
            model=f"aciga.{device.physics_id}.{device.model_type}",
            serial_number = device.eq_uid,
            manufacturer="aciga",
            sw_version="v1.1",
            hw_version="v1.0",
            configuration_url = device.icon_url,
            suggested_area=device.room_name,
            connections={(dr.CONNECTION_NETWORK_MAC, device.eq_number)}
        )
        # 将设备信息添加到 hass.data 中
        hass.data[DOMAIN]['devices'][config_entry.entry_id].append(device)

    # 注册其它实体
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """卸载配置条目。"""
    await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    # 清理任何注册的组件或服务
    hass.data[DOMAIN].pop('devices', None)  # 清除设备数据
    """Unload a config entry."""
    data = hass.data[DOMAIN].get(config_entry.entry_id)
    if data is not None:
        hass.data[DOMAIN].pop(config_entry.entry_id)
    return True
    
async def async_reload_entry(hass: HomeAssistant, config_entry: ConfigEntry)-> None:
    """处理配置更新。"""
    await hass.config_entries.async_reload(config_entry.entry_id)
    
async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry , device_entry: dr.DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    device_registry.async_get(hass).async_remove_device(device_entry.id)
    return True