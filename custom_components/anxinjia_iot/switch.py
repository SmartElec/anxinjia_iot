'''
Description: 
Version: 2.0
Autor: miaoguoqiang
Date: 2025-02-24 20:02:36
LastEditors: miaoguoqiang
LastEditTime: 2025-03-24 09:27:08
'''
import logging
import asyncio
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.switch import SwitchEntity,SwitchDeviceClass
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from .const import DOMAIN,CONF_TOKEN
from .api import async_Control_SwitchOrLight,async_get_all_devices_status
#from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class AnxinJiaSwitch(SwitchEntity):
    def __init__(self, device, virtual_model):
        self._device = device
        
        self.is_virtual = virtual_model.get("is_virtual", False)
        if self.is_virtual:
            self._name = virtual_model.get("virtualName")  # 只使用虚拟名称
        else:
            self._name = f"{device.room_name}{virtual_model.get('virtualName')}"  # 使用房间名称和虚拟名称

        self._unique_id = virtual_model.get("virtualNumber")  # 使用 Device 类的 unique_id 属性
        self._model_type = virtual_model.get("modelType")  # 获取设备的模型类型
        self._state = False  # 默认状态
        self._attr_device_class = SwitchDeviceClass.SWITCH
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
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def is_on(self):
        return self._state
        
    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        if self.is_virtual:
            # 虚拟开关打开状态
            self._state = True
            self.async_schedule_update_ha_state()  # 更新状态到 Home Assistant
            _LOGGER.debug("虚拟开关已打开")

            # 等待2秒后自动关闭
            await asyncio.sleep(2)
            await self.async_turn_off()  # 关闭虚拟开关
        else:
            # 对于实际开关，调用原有的 API 控制逻辑
            try:
                # 调用 api.py 中的异步函数
                result = await async_Control_SwitchOrLight(self._name,self._unique_id,self._model_type, True)
                # 处理 result，记录日志或更新状态
                if result:
                    self._state = True
                    _LOGGER.debug("设备已打开")

                _LOGGER.info(f"switch on API 调用成功: {result}")
            except Exception as e:
                _LOGGER.error(f"switch on API 调用失败: {e}")

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        if self.is_virtual:
            # 虚拟开关直接关闭状态并更新 Home Assistant
            self._state = False
            self.async_schedule_update_ha_state()  # 更新 Home Assistant 状态
            _LOGGER.debug("虚拟开关已关闭")
        else:
            # 对于实际开关，调用原有的 API 控制逻辑
            try:
                # 调用 api.py 中的异步函数
                result = await async_Control_SwitchOrLight(self._name,self._unique_id,self._model_type, False)
                # 处理 result，记录日志或更新状态
                if result:
                    self._state = False
                    _LOGGER.debug("设备已关闭")

                _LOGGER.info(f"switch off API 调用成功: {result}")
            except Exception as e:
                _LOGGER.error(f"switch off API 调用失败: {e}")

    async def async_will_remove_from_hass(self):
        # 停止定时更新
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None

    async def async_added_to_hass(self):
        """Entity is added to Home Assistant."""
        self._attr_icon = "mdi:ceiling-light-outline"
        #self._unsub_timer = async_track_time_interval(
        #    self.hass, self._async_update_devices, timedelta(seconds=120)
        #)
        await super().async_added_to_hass()
        _LOGGER.debug(f"Entity added to hass: {self.hass}")
        
    async def async_update(self):
        """Update the device state (e.g., call status query API)."""
        # 这里实现查询设备状态的逻辑
        pass

async def async_update_devices(hass: HomeAssistant, eq_numbers: list[str], entities: list[AnxinJiaSwitch]):
    """
    定时更新所有设备的状态。

    :param hass: Home Assistant 核心实例
    :param eq_numbers: 设备的 eqNumber 列表
    :param entities: 设备实体列表
    """
    try:
        # 调用 async_get_all_devices_status 获取所有设备状态
        all_devices_status = await async_get_all_devices_status(eq_numbers)
        if all_devices_status is not None:
            _LOGGER.debug(f"Success fetch device statuses: {all_devices_status}")
            # 遍历所有实体，更新状态
            for entity in entities:
                if not entity.is_virtual:
                    # 从返回的状态字典中获取对应实体的状态
                    device_status = all_devices_status.get(entity._unique_id)
                    if device_status is not None:
                        # 更新实体的状态
                        entity._state = device_status
                        _LOGGER.debug(f"Updated device state for {entity._name}: {entity._state}")
                    else:
                        _LOGGER.warning(f"No status found for device {entity._unique_id}")
        else:
            _LOGGER.error("Failed to fetch device statuses")
    except Exception as e:
        _LOGGER.error(f"Error updating device states: {e}")
        
async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AnxinJia switches from a config entry."""
    devices = hass.data[DOMAIN]['devices'][config_entry.entry_id]

    # 提取 model_type 为 102001 的设备的 eqNumber
    eq_numbers = [
        device.eq_number 
        for device in devices 
        if device.model_type == 102001
    ]
    
    # 创建实体列表
    new_entities = []
    
    # 遍历设备列表，创建 AnxinJiaSwitch 实例
    for device_info in devices:
        # 替换为适当的属性访问
        #_LOGGER.debug(f"Model Type: {device_info.model_type}, Type: {type(device_info.model_type)}")
        if device_info.model_type == 102001:
            for virtual_model in device_info.virtual_models:  # 确保使用正确的属性名称
                actual_switch  = AnxinJiaSwitch(device_info, virtual_model)
                new_entities.append(actual_switch )
        # 如果设备模型类型是 101001，则添加相应的虚拟开关
        if device_info.model_type == 101001:
            for i in range(1, 5):  # 创建四个虚拟开关
                virtual_model = {
                    "virtualName": f"场景模式{i}",
                    "virtualNumber": f"virtual_switch_{i}",
                    "modelType": 101001,
                    "is_virtual": True,
                }
                entity = AnxinJiaSwitch(device_info, virtual_model)
                new_entities.append(entity)

    # 异步添加实体到平台
    if new_entities:
        async_add_entities(new_entities, update_before_add=True)

    # 添加全局定时器以更新所有设备状态
    async def device_update_timer(now):
        await async_update_devices(hass, eq_numbers, new_entities)

    # 
    async_track_time_interval(hass, device_update_timer, timedelta(seconds=60))