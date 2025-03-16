'''
Description: file content
Version: 2.0
Autor: miaoguoqiang
Date: 2025-02-25 12:13:31
LastEditors: miaoguoqiang
LastEditTime: 2025-03-04 16:31:39
'''
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.button import ButtonEntity,ButtonDeviceClass
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN,CONF_TOKEN
from .api import async_get_SceneService
from .api import async_run_SceneService

_LOGGER = logging.getLogger(__name__)
        
async def async_setup_entry(
    hass: HomeAssistant, 
    config_entry: ConfigEntry, 
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up button entities from a config entry."""
    devices = hass.data[DOMAIN]['devices'][config_entry.entry_id]
    if not devices:
        _LOGGER.warn("无法获取设备信息-BTN")
        return  # 处理设备信息缺失
    
    #user_id = config_entry.data.get(CONF_USER_ID)
    addressId = hass.data[DOMAIN].get('addressId')

    if addressId is None:
        _LOGGER.warn("没有找到有效的 addressId")
        return
    
    # 继续进行其他逻辑...
    _LOGGER.info(f"获取到的 addressId: {addressId}")

    # 使用 houseId 获取场景信息
    scenes = await async_get_SceneService( addressId)  
    if scenes is None:
        _LOGGER.warn("没有获取到场景信息")
        return  

    # 注册按钮实体
    new_buttons_entities = []

    # 遍历设备列表，创建 AnxinJiaButton 实例
    for device_info in devices:
        if device_info.model_type == 101001:
            for scene in scenes:
                scene_id = scene.get("id")
                scene_name = scene.get("sceneName")
                button = AnxinJiaButton(device_info,scene_name, scene_id)
                new_buttons_entities.append(button)
            # 满足条件后退出循环
            break  # 退出设备循环，只要找到一个符合条件的 device_info 就退出
        
    # 使用 async_add_entities 注册按钮实体
    if new_buttons_entities:
        async_add_entities(new_buttons_entities)
    
class AnxinJiaButton(ButtonEntity):
    """Representation of a custom button entity."""

    def __init__(self, device, name: str, unique_id: str):
        """Initialize the button."""
        self._device = device
        self._name = name
        self._unique_id = unique_id
        #self._attr_device_class = ButtonDeviceClass.IDENTIFY
        self._model_type = device.model_type
        self._attr_unique_id = self._unique_id  # 确保唯一标识符
        self._attr_name = self._name  # 实体名称
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.eq_number)},  # 设备的唯一标识符
            "name": device.name ,  # 设备名称
            "manufacturer": "aciga",  # 制造商
            "model": self._model_type,  # 设备型号
            "sw_version": "v1.0",  # 软件版本
        }

    @property
    def name(self) -> str:
        """Return the name of the button."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID for this button."""
        return self._unique_id

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # 调用 api.py 中的异步函数
            result = await async_run_SceneService(self._unique_id,self._name)
            # 处理 result，记录日志或更新状态
            _LOGGER.info(f"BTN API 调用成功: {result}")
        except Exception as e:
            _LOGGER.info(f"Scene ID: {self._unique_id}")
            _LOGGER.error(f"BTN API 调用失败: {e}")

    async def async_added_to_hass(self):
        """Called when the entity is added to hass for initialization or state update."""
        # 可以选择在这里执行一些初始化逻辑
        pass
