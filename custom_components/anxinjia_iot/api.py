'''
Description: 
Version: 2.0
Autor: miaoguoqiang
Date: 2025-02-24 22:16:11
LastEditors: miaoguoqiang
LastEditTime: 2025-03-12 16:46:42
'''
import aiohttp
import asyncio
import logging
import requests
import hashlib
import json
import time
import logging
from typing import Optional
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN,CONF_TOKEN,CONF_USER_ID

# 创建 logger 实例
_LOGGER = logging.getLogger(__name__)

async def fetch_AddressId_Devices(access_token:str, addressId:str,retries: int = 3):

    IMPORT_AddrDevice_URL = "https://service.aciga.com.cn/IntelligentHome/addressDeviceManagement/addressDevice/pageList"
    if access_token is None:
        _LOGGER.error("Token 无效")
        return None

    _LOGGER.debug("开始获取导入设备列表...")

    # 构建请求头
    headers = {
        "Authorization": access_token,
        "Content-Type": "application/json; charset=utf-8",
        "traceId": generate_trace_id()
    }

    # 构建请求体
    payload = {
      "addressId": addressId,
      "fullFlag": True,
      "pageNo": 100,
      "pageSize": 20
    }
    last_exception = None  # 存储最后一次异常
    timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=60)
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(IMPORT_AddrDevice_URL, headers=headers, json=payload, timeout=timeout) as response:
                    response.raise_for_status()  # 检查 HTTP 状态码
                    response_json = await response.json()
                    if response_json.get("success"):
                        lists = response_json.get("data") or None
                        if lists:
                            devices = lists.get("list")
                            _LOGGER.debug(f"导入设备列表请求成功:{response_json}")
                            return devices
                        else:
                            _LOGGER.debug(f"导入设备列表 为空:{response_json}")
                            return None
                    else:
                        _LOGGER.error("导入设备信息失败, 原因: %s", response_json.get("msg"))
                        return None
        except aiohttp.ClientResponseError as e:
            if e.status in {400, 401, 403, 404}:
                _LOGGER.warning(f"导入设备时请求失败 - {e.status}: {e.message}")
                if e.status == 401:
                    raise TokenExpiredError("Access token has expired.")
                else:
                    last_exception = e
                    # 不抛出异常，继续重试
            else:
                _LOGGER.warning(f"导入设备时服务器错误: {e.status}, 尝试重试 {attempt + 1}/{retries}")
                last_exception = e
        except aiohttp.ClientError as e:  # 捕获所有 aiohttp 的异常，包括连接错误和超时
            _LOGGER.warning(f"导入设备时连接失败: {e}, 尝试重试 {attempt + 1}/{retries}")
            last_exception = e
        except Exception as e:
            _LOGGER.warning(f"导入设备时发生未知错误: {e}, 不进行重试。")
            last_exception = e
            break
        finally:
            await asyncio.sleep(2)  # 可选：在重试之间等待一段时间

    # 如果所有尝试都失败,记录最后的异常
    if last_exception:
        _LOGGER.error(f"导入设备信息失败,最后的异常: {last_exception}")
    return None

async def fetch_user_devices(access_token:str, retries: int = 3):

    IMPORT_UserDevice_URL = "https://service.aciga.com.cn/IntelligentHome/addressDeviceManagement/userDevice/needImport"
    if access_token is None:
        _LOGGER.error("Token 无效")
        return None

    _LOGGER.debug("开始获取导入设备列表...")

    # 构建请求头
    headers = {
        "Authorization": access_token,
        "Content-Type": "application/json; charset=utf-8",
        "traceId": generate_trace_id()
    }

    # 构建请求体
    payload = {
        "pageNo": 1,
        "pageSize": 100
    }
    last_exception = None  # 存储最后一次异常
    timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=60)
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(IMPORT_UserDevice_URL, headers=headers, json=payload, timeout=timeout) as response:
                    response.raise_for_status()  # 检查 HTTP 状态码
                    response_json = await response.json()
                    if response_json.get("success"):
                        devices = response_json.get("data") or None
                        _LOGGER.debug(f"导入设备列表请求成功:{response_json}")
                        return devices
                    else:
                        _LOGGER.error("导入设备信息失败, 原因: %s", response_json.get("msg"))
                        return None
        except aiohttp.ClientResponseError as e:
            if e.status in {400, 401, 403, 404}:
                _LOGGER.warning(f"导入设备时请求失败 - {e.status}: {e.message}")
                if e.status == 401:
                    raise TokenExpiredError("Access token has expired.")
                else:
                    last_exception = e
                    # 不抛出异常，继续重试
            else:
                _LOGGER.warning(f"导入设备时服务器错误: {e.status}, 尝试重试 {attempt + 1}/{retries}")
                last_exception = e
        except aiohttp.ClientError as e:  # 捕获所有 aiohttp 的异常，包括连接错误和超时
            _LOGGER.warning(f"导入设备时连接失败: {e}, 尝试重试 {attempt + 1}/{retries}")
            last_exception = e
        except Exception as e:
            _LOGGER.warning(f"导入设备时发生未知错误: {e}, 不进行重试。")
            last_exception = e
            break
        finally:
            await asyncio.sleep(2)  # 可选：在重试之间等待一段时间

    # 如果所有尝试都失败,记录最后的异常
    if last_exception:
        _LOGGER.error(f"导入设备信息失败,最后的异常: {last_exception}")
    return None

async def fetch_devices(hass: HomeAssistant, config_entry: ConfigEntry):
    access_token = config_entry.data.get(CONF_TOKEN)
    user_id = config_entry.data.get(CONF_USER_ID)

    userInfo = await getUserDetailById(access_token,user_id)
    if userInfo is None:
        return None

    telephone = userInfo.get("userPhone")

    DefaultRoomInfo = await Get_Default_Room(access_token,user_id)
    if DefaultRoomInfo:
        addressId = DefaultRoomInfo.get("addressId")

    if addressId is None:
        return None

    hass.data[DOMAIN]['addressId'] = addressId

    devices = await fetch_user_devices(access_token)
    if devices:
        return devices    

    result = await async_active_addressId(access_token,addressId)
    if result == False:
        return None

    result = await factory_token_get(access_token,28,telephone)
    if result == False:
        return None
    result = await async_GetFloorDevice(access_token,addressId)
    if result == False:
        return None

    result = await factory_token_get(access_token,5,telephone)
    if result == False:
        return None
    result = await async_active_addressId(access_token,addressId)
    if result == False:
        return None

    result = await factory_token_get(access_token,1,telephone)
    if result == False:
        return None
    devices = await fetch_AddressId_Devices(access_token,addressId)
    #if devices is None:
    #    devices = fetch_user_devices(access_token)

    return devices

async def factory_token_get(access_token:str,supplierType:int,telephone:str)->bool:
    FACTORY_TOKEN_GET_URL ="https://service.aciga.com.cn/IntelligentHome/userToken/factory/getToken"
    # 构建请求头
    headers = {
        "Authorization": access_token,
        "Content-Type": "application/json; charset=utf-8",
        "traceId":generate_trace_id()
    }
    payload = {
        "supplierType": supplierType,
        "telephone":telephone
    }
    try:
        # 创建一个 timeout 对象
        timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(FACTORY_TOKEN_GET_URL, headers=headers, json=payload, timeout=timeout) as response:
                response.raise_for_status()  # 如果响应状态码不是 200，会抛出异常
                response_json = await response.json()

                # 确保响应中有 'success' 字段
                if "success" in response_json:
                    if response_json["success"]:
                        _LOGGER.info(f"FACTORY_TOKEN[{supplierType}] 成功！")
                        return True
                    else:
                        _LOGGER.error(f"FACTORY_TOKEN[{supplierType}]{telephone} 失败, 响应: {response_json}")
                else:
                    _LOGGER.error(f"FACTORY_TOKEN[{supplierType}]{telephone} 响应中缺少 'success' 字段, 响应: {response_json}")

    except aiohttp.ClientResponseError as e:
        _LOGGER.error(f"FACTORY_TOKEN[{supplierType}]{telephone} 请求失败 - {e.status}: {e.message}")
    except aiohttp.ClientError as e:
        _LOGGER.error(f"FACTORY_TOKEN[{supplierType}]{telephone} 连接失败: {e}, 建议重试")
    except Exception as e:
        # 捕获所有其他未知异常
        _LOGGER.error(f"FACTORY_TOKEN[{supplierType}]{telephone} 发生未知错误: {e}")

    return False  # 在发生错误或失败时返回 False

async def accountEqHouse(telephone:str)->bool:
    url ="https://service.aciga.com.cn/IntelligentHome/intelligenthomeUser/accountEqHouse"
    headers = {
        "Authorization": access_token,
        "Content-Type": "application/json; charset=utf-8",
        "traceId":generate_trace_id(),
        "Connection":"Keep-Alive"
    }
    payload = {
      "telephone": telephone
    }
    try:
        # 创建一个 timeout 对象
        timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload, timeout=timeout) as response:
                response.raise_for_status()  # 如果响应状态码不是 200，会抛出异常
                response_json = await response.json()

                # 确保响应中有 'success' 字段
                if "success" in response_json:
                    if response_json["success"]:
                        _LOGGER.info(f"accountEqHouse 成功！")
                        return True
                    else:
                        _LOGGER.error(f"accountEqHouse 失败, 响应: {response_json}")
                else:
                    _LOGGER.error(f"accountEqHouse 响应中缺少 'success' 字段, 响应: {response_json}")

    except aiohttp.ClientResponseError as e:
        _LOGGER.error(f"accountEqHouse 请求失败 - {e.status}: {e.message}")
    except aiohttp.ClientError as e:
        _LOGGER.error(f"accountEqHouse 连接失败: {e}, 建议重试")
    except Exception as e:
        # 捕获所有其他未知异常
        _LOGGER.error(f"accountEqHouse 发生未知错误: {e}")

    return False  # 在发生错误或失败时返回 False

async def Get_Default_Room(access_token:str,userId:str):
    DEFAULT_ROOM_URL ="https://service.aciga.com.cn/service-user/service-user/aot/userRoom/getDefaultRoom"

    # 构建请求头
    headers = {
        "Authorization": access_token,
        "Content-Type": "application/json; charset=utf-8",
        "traceId":generate_trace_id(),
        "Connection":"Keep-Alive"
    }
    payload = {
        "userId": userId
    }
    try:
        # 创建一个 timeout 对象
        timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(DEFAULT_ROOM_URL, headers=headers, json=payload, timeout=timeout) as response:
                response.raise_for_status()  # 如果响应状态码不是 200，会抛出异常
                response_json = await response.json()

                if response_json.get("code")==0:
                    devices = response_json.get("data")
                    _LOGGER.debug(f"获取默认地址成功:{devices}")
                    return devices or None
                else:
                    _LOGGER.error(f"获取默认地址失败, 响应: {response_json}")

    except aiohttp.ClientResponseError as e:
        _LOGGER.error(f"获取默认地址请求失败 - {e.status}: {e.message}")
    except aiohttp.ClientError as e:
        _LOGGER.error(f"获取默认地址连接失败: {e}, 建议重试")
    except Exception as e:
        # 捕获所有其他未知异常
        _LOGGER.error(f"获取默认地址 发生未知错误: {e}")

    return None  # 在发生错误或失败时返回 None 

async def async_active_addressId(access_token:str,addressId:str)->bool:
    ACTIVE_ADDRESS_URL ="https://service.aciga.com.cn/IntelligentHome/addressDeviceManagement/addressId/active"
    headers = {
        "Authorization": access_token,
        "Content-Type": "application/json; charset=utf-8",
        "traceId":generate_trace_id()
    }
    payload = {
        "addressId": addressId
    }
    try:
        # 创建一个 timeout 对象
        timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(ACTIVE_ADDRESS_URL, headers=headers, json=payload, timeout=timeout) as response:
                response.raise_for_status()  # 如果响应状态码不是 200，会抛出异常
                response_json = await response.json()
                if response_json.get("success")==True:
                    _LOGGER.info(f"选择地址{addressId}成功！")
                    return True
                else:
                    _LOGGER.error(f"选择地址{addressId}失败, 响应: {response_json}")
    except aiohttp.ClientResponseError as e:
        _LOGGER.error(f"选择地址{addressId}请求失败 - {e.status}: {e.message}")
    except aiohttp.ClientError as e:
        _LOGGER.error(f"选择地址{addressId}连接失败: {e}, 建议重试")
    except Exception as e:
        # 捕获所有其他未知异常
        _LOGGER.error(f"选择地址{addressId} 发生未知错误: {e}")

    return False  # 在发生错误或失败时返回 False 

async def async_GetFloorDevice(access_token:str,addressId:str)->bool:
    url ="https://service.aciga.com.cn/IntelligentHome/addressDeviceManagement/addressFloorDevice/list"
    if access_token is None:
        _LOGGER.error("Token 无效")
        return None

    _LOGGER.debug("开始获取导入设备列表...")

    # 构建请求头
    headers = {
        "Authorization": access_token,
        "Content-Type": "application/json; charset=utf-8",
        "traceId": generate_trace_id()
    }

    # 构建请求体
    payload = {
      "addressId": addressId,
      "fullFlag": True
    }
    try:
        # 创建一个 timeout 对象
        timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload, timeout=timeout) as response:
                response.raise_for_status()  # 如果响应状态码不是 200，会抛出异常
                response_json = await response.json()

                # 确保响应中有 'success' 字段
                if "success" in response_json:
                    if response_json["success"]:
                        _LOGGER.info(f"获取楼层信息成功！")
                        return True
                    else:
                        _LOGGER.error(f"获取楼层信息失败, 响应: {response_json}")
                else:
                    _LOGGER.error(f"获取楼层信息响应中缺少 'success' 字段, 响应: {response_json}")

    except aiohttp.ClientResponseError as e:
        _LOGGER.error(f"获取楼层信息请求失败 - {e.status}: {e.message}")
    except aiohttp.ClientError as e:
        _LOGGER.error(f"获取楼层信息连接失败: {e}, 建议重试")
    except Exception as e:
        # 捕获所有其他未知异常
        _LOGGER.error(f"获取楼层信息 发生未知错误: {e}")

    return False  # 在发生错误或失败时返回 False

async def async_get_all_devices_status(eq_numbers:list[str], access_token: str)-> Optional[dict[str, bool]]:
    """
    从 API 获取所有设备状态，并解析出每个虚拟设备的 isonoff 状态。

    :param access_token: 用于 API 认证的访问令牌
    :param eq_numbers: 设备的 eqNumber 列表
    :return: 一个字典，键为虚拟设备的 unique_id，值为布尔状态（True 或 False）
    """
    GET_STATUS_URL = "https://service.aciga.com.cn/IoT/smart-device/model/v1/nowStatus/eqNumberBatch"
    try:
        # 将 eqNumber 列表组合成 payload
        payload = {
            "eqNumbers": eq_numbers
        }

        # 调用 API 获取设备状态
        # 构建请求头
        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json; charset=utf-8",
            "traceId": generate_trace_id()
        }
        timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(GET_STATUS_URL, headers=headers, json=payload) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        data = response_data.get("data", [])
                        status_dict = {}

                        # 遍历每个设备
                        for device in data:
                            eq_number = device.get("eqNumber")
                            virtual_devices = device.get("virtualNumberStatusVoList", [])

                            # 遍历每个虚拟设备
                            for virtual_device in virtual_devices:
                                virtual_number = virtual_device.get("virtualNumber")
                                status_list = virtual_device.get("statusList", {})

                                # 获取 isonoff 状态
                                isonoff = status_list.get("isonoff")
                                if isonoff is not None:
                                    status_dict[virtual_number] = isonoff == "1"  # 转换为布尔值
                        return status_dict
                    else:
                        _LOGGER.error(f"API fetch device request failed: {response_data.get('msg')}")
                        return None
                else:
                    _LOGGER.error(f"Failed to fetch device status: HTTP {response.status}")
                    return None
    except Exception as e:
        _LOGGER.error(f"Error fetching device status: {e}")
        return None

async def async_Control_switch(access_token:str,dev_name:str,unique_id:str,model_type:int, is_open:bool)->bool:
    """发送控制请求到设备"""
    CONTROL_SW_URL = "https://service.aciga.com.cn/IoT/smart-control/job/createJob"
    # 构建请求头
    headers = {
        "Authorization": access_token,
        "Content-Type": "application/json; charset=utf-8",
        "traceId": generate_trace_id()
    }
    payload = None

    if model_type == 102001:  # 灯具开关
        payload = {
            "type": "SET_PROPERTY",
            "timeoutConfig": {
                "num": 0,
                "inProgressTimeoutInMinutes": 0
            },
            "jobDocument": {
                "params": [
                    {
                        "onoff": 1 if is_open else 0
                    }
                ]
            },
            "virtualNumber": unique_id
        }
    else:
        _LOGGER.error(f"未处理的设备类型: {type(model_type)} {model_type}")
        return False

    try:
        # 创建一个 timeout 对象
        timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(CONTROL_SW_URL, headers=headers, json=payload, timeout=timeout) as response:
                response.raise_for_status()  # 如果响应状态码不是 200，会抛出异常
                response_json = await response.json()

                # 确保响应中有 'success' 字段
                if "success" in response_json:
                    if response_json["success"]:
                        _LOGGER.info(f"控制 {dev_name} {'打开' if is_open else '关闭'}成功！")
                        return True
                    else:
                        _LOGGER.error(f"控制 {dev_name} 失败, 响应: {response_json}")
                else:
                    _LOGGER.error(f"控制 {dev_name} 响应中缺少 'success' 字段, 响应: {response_json}")

    except aiohttp.ClientResponseError as e:
        _LOGGER.error(f"控制 {dev_name} 请求失败 - {e.status}: {e.message}")
    except aiohttp.ClientError as e:
        _LOGGER.error(f"控制 {dev_name} 连接失败: {e}, 建议重试")
    except Exception as e:
        # 捕获所有其他未知异常
        _LOGGER.error(f"控制 {dev_name} 发生未知错误: {e}")

    return False  # 在发生错误或失败时返回 False

async def async_Control_cover(access_token:str,dev_name:str,unique_id:str,model_type:int, opt_means:str)->bool:
    """发送控制请求到设备"""
    CONTROL_COVER_URL = "https://service.aciga.com.cn/IoT/smart-control/job/createJob"
    # 构建请求头
    headers = {
        "Authorization": access_token,
        "Content-Type": "application/json; charset=utf-8",
        "traceId": generate_trace_id()
    }
    payload = None

    if model_type == 102004:  # 窗帘设备
        payload = {
            "desc": "控制窗帘",
            "jobDocument": {
                "inputData": {
                    "opt_means": opt_means
                },
                "serviceCode": "curtain_opt"
            },
            "type": "INVOKE_SERVICE",
            "timeoutConfig": {
                "inProgressTimeoutInSeconds": 0,
                "num": 0
            },
            "virtualNumber": unique_id
        }
    else:
        _LOGGER.error(f"未处理的设备类型: {type(model_type)} {model_type}")
        return False

    try:
        # 创建一个 timeout 对象
        timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(CONTROL_COVER_URL, headers=headers, json=payload, timeout=timeout) as response:
                response.raise_for_status()  # 如果响应状态码不是 200，会抛出异常
                response_json = await response.json()

                # 确保响应中有 'success' 字段
                if "success" in response_json:
                    if response_json["success"]:
                        _LOGGER.info(f"控制 {dev_name} {opt_means}成功！")
                        return True
                    else:
                        _LOGGER.error(f"控制 {dev_name} 失败, 响应: {response_json}")
                else:
                    _LOGGER.error(f"控制 {dev_name} 响应中缺少 'success' 字段, 响应: {response_json}")

    except aiohttp.ClientResponseError as e:
        _LOGGER.error(f"控制 {dev_name} 请求失败 - {e.status}: {e.message}")
    except aiohttp.ClientError as e:
        _LOGGER.error(f"控制 {dev_name} 连接失败: {e}, 建议重试")
    except Exception as e:
        # 捕获所有其他未知异常
        _LOGGER.error(f"控制 {dev_name} 发生未知错误: {e}")

    return False  # 在发生错误或失败时返回 False 

async def getUserDetailById(access_token:str,customId:str):
    USER_INFO_URL = "https://service.aciga.com.cn/service-user/service-user/aot/user/v1/getUserDetailById"
    # 构建请求头
    headers = {
        "Authorization": access_token,
        "Content-Type": "application/json; charset=utf-8",
        "traceId": generate_trace_id()
    }
    payload = {
        "id": customId,
        "showPhone":True
    }
    try:
        timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(USER_INFO_URL, headers=headers, json=payload) as response:
                response.raise_for_status()
                response_json = await response.json()
                if response_json.get("code") == 0:
                    _LOGGER.info("获取用户信息成功！")
                    return response_json.get("data") or None
                else:
                    _LOGGER.error(f"用户信息请求失败,原因: {response_json.get('msg')}")

    except aiohttp.ClientResponseError as e:        
        _LOGGER.error(f"获取用户信息时请求失败 - {e.status}: {e.message}")
    except aiohttp.ClientError as e:
        _LOGGER.error(f"获取用户信息时连接失败: {e}, 建议重试")
    except Exception as e:
        # 捕获所有其他未知异常
        _LOGGER.error(f"获取用户信息时发生未知错误: {e}")

    return None

async def async_get_SceneService(access_token: str, addressId: str):
    QrySceneUrl = "https://service.aciga.com.cn/SceneService/scene/qryScene"
    """Asynchronously get scene service request."""
    # 构建请求头
    headers = {
        "Authorization": access_token,
        "Content-Type": "application/json; charset=utf-8",
        "traceId": generate_trace_id()
    }

    # 构建请求体
    payload = {
        "addressId": addressId
    }
    try:
        timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(QrySceneUrl, headers=headers, json=payload) as response:
                response.raise_for_status()
                response_json = await response.json()
                if response_json.get("success"):
                    _LOGGER.info("获取快捷操作请求成功！")
                    return response_json.get("data") or None
                else:
                    _LOGGER.error(f"获取快捷操作请求失败,原因: {response_json.get('msg')}")

    except aiohttp.ClientResponseError as e:        
        _LOGGER.error(f"获取场景时请求失败 - {e.status}: {e.message}")
    except aiohttp.ClientError as e:
        _LOGGER.error(f"获取场景时连接失败: {e}, 建议重试") 
    except Exception as e:
        # 捕获所有其他未知异常
        _LOGGER.error(f"获取场景时发生未知错误: {e}")

    return None

async def async_run_SceneService(access_token: str, SceneId: str, SceneName: str)-> None:
    """Asynchronously get scene service request."""
    RunSceneurl = "https://service.aciga.com.cn/SceneService/ctrl/runScene"
    # 构建请求头
    headers = {
        "Authorization": access_token,
        "Content-Type": "application/json; charset=utf-8",
        "traceId": generate_trace_id()
    }

    # 构建请求体
    payload = {
            "id": SceneId  # 使用 unique_id 作为 SceneId
        }

    try:
        timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(RunSceneurl, headers=headers, json=payload) as response:
                response.raise_for_status()
                response_json = await response.json()
                if response_json.get("success"):
                    _LOGGER.info(f"控制设备 '{SceneName}' 按钮按下成功！")
                else:
                    _LOGGER.error(f"控制设备 '{SceneName}' 失败,响应: {response_json}")
    except aiohttp.ClientResponseError as e:      
        _LOGGER.error(f"控制设备 '{SceneName}' 时请求失败 - {e.status}: {e.message}")          
    except aiohttp.ClientError as e:
        _LOGGER.error(f"控制设备 '{SceneName}' 时连接失败: {e}, 建议重试") 
    except Exception as e:
        _LOGGER.error(f"控制设备 '{SceneName}' 时发生错误: {e}")


async def async_login_auth2(username, password):
    """
    整合后的统一登录认证函数 
    参数：
        username - 登录用户名（字符串）
        password - 登录密码（字符串）
    返回：
        access_token - 成功时返回访问令牌,失败返回None 
    """

    # 使用 aiohttp 异步请求第一个 API 获取 auth_metadata
    timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.post('http://typecho.dns.army:3005/auth_metadata', json={'username': username, 'password': password}) as response:
                response.raise_for_status()  # 检查响应状态
                auth_response = await response.json()
                auth_metadata = auth_response.get('auth_metadata')
                request_url = auth_response.get('request_url')
                hashed_pwd = auth_response.get('password')

                if not auth_metadata or not request_url:
                    _LOGGER.error("获取 auth_metadata 或 request_url 失败")
                    return None

                headers = {
                    "authMetaData": auth_metadata,
                    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
                }

                payload = f"username={username}&password={hashed_pwd}"
                _LOGGER.debug(f"[NETWORK] 准备请求：{request_url[:60]}...")

                # 发送认证请求
                async with session.post(request_url, headers=headers, data=payload) as auth_response:
                    auth_response.raise_for_status()
                    resp_data = await auth_response.json()

                    if resp_data.get("success"): 
                        _LOGGER.info("[SUCCESS] 认证成功,获取到访问令牌")
                        return resp_data.get("data") or None
                    else:
                        _LOGGER.error(f"认证失败：{resp_data.get('msg', '未知错误')}")
                        return None

        except aiohttp.ClientResponseError as e:
            _LOGGER.error(f"认证时请求失败 - {e.status}: {e.message}")
        except aiohttp.ClientError as e:
            _LOGGER.error(f"认证时连接失败: {e}, 建议重试") 
        except Exception as e:
            # 捕获所有其他未知异常
            _LOGGER.error(f"认证时发生未知错误: {e}")

    return None

def generate_trace_id(prefix="ACIGAd5cf6ed6d01aaa09")->str:
    """Generate a unique trace ID based on the current timestamp.

    Args:
        prefix (str): The prefix for the trace ID.

    Returns:
        str: A formatted trace ID.
    """
    # 获取当前时间的纳秒时间戳
    microsecond_timestamp = time.time_ns()

    # 将时间戳转换为字符串并填充零
    formatted_timestamp = str(microsecond_timestamp).zfill(17)

    # 确保时间戳不超过17位
    if len(formatted_timestamp) > 17:
        formatted_timestamp = formatted_timestamp[-17:]

    # 生成最终的 trace ID
    trace_id = f"{prefix}{formatted_timestamp}"
    return trace_id

class TokenExpiredError(Exception):
    """Custom exception for expired tokens."""
    pass