from asyncio import sleep
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse, JSONResponse
from httpx import AsyncClient, TimeoutException, HTTPStatusError, Limits
from json import loads
from sqlalchemy.orm import Session
from typing import Optional
from urllib.parse import urlparse
from uuid import uuid4

from config.env import AgentConfig
from config.get_db import get_db
from module_admin.service.login_service import LoginService
from utils.log_util import *
from utils.response_util import ResponseUtil

# 取消全局依赖，便于从 query/header 中自行解析 token
agentController = APIRouter(prefix='/agent')


def trust_env_proxy(url):
    """
    是否信任环境代理
    """
    parsed = urlparse(url)
    agent_host = (parsed.hostname or "").lower()
    use_trust_env = True
    if agent_host in AgentConfig.INTERNAL_HOST_SET or any(
            agent_host.endswith(s) for s in AgentConfig.K8S_INTERNAL_SUFFIXES):
        use_trust_env = False
    return use_trust_env


async def parse_cur_user_and_token(
        request: Request,
        request_id: str,
        token_param: Optional[str],
        query_db: Session
):
    """
    解析当前用户和token
    
    返回: (user_name, token) 或 None（如果token校验失败）
    """
    # 获取token（从URL参数或请求头），支持 Bearer 开头或纯token
    token = token_param or request.query_params.get('token') \
            or request.headers.get('Authorization', '').replace('Bearer ', '')

    # 解析当前用户（如果提供了 token 但校验失败，返回None）
    current_user = None
    if token:
        try:
            # LoginService.get_current_user 期望 Bearer 开头
            bearer_token = token if token.startswith('Bearer') else f"Bearer {token}"
            current_user = await LoginService.get_current_user(request, token=bearer_token, query_db=query_db)
        except Exception as e:
            logger.warning(f"[{request_id}] token校验失败: {str(e)}")
            return None  # 返回None表示校验失败

    user_name = getattr(getattr(current_user, 'user', None), 'user_name', 'guest')
    return user_name, token


async def stream_agent_response(
        agent_url: str,
        params: dict,
        token: Optional[str],
        request_id: str,
        log_prefix: str = "Agent"
):
    """通用的SSE流式响应生成器"""
    try:
        # 注意：由上游服务负责发送 chatId 给前端（避免重复）。这里不再预先发送 chatId。
        # 使用httpx异步客户端调用Agent服务，配置连接池限制

        async with AsyncClient(
                timeout=AgentConfig.LITEMIND_AGENT_TIMEOUT,
                limits=Limits(max_keepalive_connections=5, max_connections=10),
                trust_env=trust_env_proxy(agent_url)
        ) as client:
            # 发送GET请求，接收SSE流
            headers = {
                "Accept": "text/event-stream",
            }
            # 如果Agent需要认证，可以传递token
            if token:
                headers["Authorization"] = f"Bearer {token}"

            # 如果上游返回 5xx，尝试一次短延迟重试；同时记录上游返回的 headers（脱敏）和 body 片段以便排查
            for attempt in range(2):
                try:
                    async with client.stream(
                            'GET',
                            agent_url,
                            params=params,
                            headers=headers
                    ) as response:
                        # 记录实际请求的完整 URL（包含 query params）和简要请求头（脱敏 token）
                        try:
                            actual_url = str(response.url)
                        except Exception:
                            actual_url = agent_url
                        safe_headers = dict(headers)
                        if 'Authorization' in safe_headers:
                            safe_headers['Authorization'] = 'Bearer ****'
                        # 支持通过配置提升该条日志到 INFO（方便线上快速排查），默认仍为 DEBUG
                        try:
                            log_level = getattr(AgentConfig, "AGENT_REQUEST_LOG_LEVEL", "DEBUG").upper()
                        except Exception:
                            log_level = "DEBUG"
                        if log_level == "INFO":
                            logger.info(
                                f"[{request_id}] 请求地址: {actual_url}, 请求头(脱敏): {safe_headers}, 参数: {params}")
                        else:
                            logger.debug(
                                f"[{request_id}] 请求地址: {actual_url}, 请求头(脱敏): {safe_headers}, 参数: {params}")

                        # 检查HTTP状态码
                        if response.status_code != 200:
                            # 尝试读取部分响应体以便排查（限制长度）
                            try:
                                raw_body = await response.aread()
                                body_snippet = raw_body[:2000].decode('utf-8', errors='replace')
                            except Exception:
                                body_snippet = "<unable to read response body>"

                            # 读取上游响应头（脱敏）
                            try:
                                headers_snippet = {k: v for k, v in dict(response.headers).items()}
                                if 'Authorization' in headers_snippet:
                                    headers_snippet['Authorization'] = 'Bearer ****'
                            except Exception:
                                headers_snippet = {}

                            error_msg = f"Agent服务返回错误状态码: {response.status_code}"
                            logger.error(
                                f"[{request_id}] {error_msg}, body: {body_snippet}, headers: {headers_snippet}")

                            # 如果是 5xx 并且是第一次尝试，则短延迟后重试一次
                            if 500 <= response.status_code < 600 and attempt == 0:
                                logger.warning(
                                    f"[{request_id}] 上游返回 {response.status_code}，准备重试一次 (attempt {attempt + 1})")
                                await sleep(0.2)
                                continue

                            # 向前端返回简洁错误信息（避免泄露过多内部信息）
                            yield f"data: {error_msg}\n\n"
                            if body_snippet:
                                yield f"data: Agent返回信息片段: {body_snippet[:300]}\n\n"
                            yield "data: [DONE]\n\n"
                            return

                        # Transparent passthrough: forward raw bytes from the Agent service to the frontend
                        # without any protocol parsing or rewriting. This preserves all SSE event
                        # boundaries and content exactly as produced by the upstream.
                        try:
                            async for chunk in response.aiter_bytes():
                                if not chunk:
                                    continue
                                # Yield the exact bytes chunk received from upstream
                                yield chunk
                        except Exception as e:
                            logger.exception(f"[{request_id}] 读取上游流时出错 (bytes passthrough): {e}")
                            # Optionally inform frontend minimally about interruption while keeping other content unchanged
                            try:
                                yield "\ndata: [ERROR] 上游数据流中断\n\n".encode("utf-8")
                            except Exception:
                                pass

                        logger.info(f"[{request_id}] {log_prefix}SSE流式响应完成（原始字节透传）")
                        # 成功处理完毕，跳出重试循环
                        break
                except Exception as e:
                    logger.exception(e)
                    if attempt == 0:
                        logger.warning(f"[{request_id}] 流式请求发生异常，准备重试一次: {str(e)}")
                        await sleep(0.2)
                        continue
                    else:
                        yield f"data: 服务暂时不可用: {str(e)}\n\n"
                        yield "data: [DONE]\n\n"
                        return

    except TimeoutException:
        logger.error(f"[{request_id}] 调用服务超时: {agent_url}")
        yield f"data: 服务响应超时，请稍后再试\n\n"
        yield "data: [DONE]\n\n"
    except HTTPStatusError as e:
        logger.error(f"[{request_id}] HTTP错误: {e.response.status_code}")
        error_msg = f"Agent服务错误: {e.response.status_code}"
        try:
            error_detail = e.response.text[:200]  # 限制错误详情长度
            if error_detail:
                error_msg += f" - {error_detail}"
        except Exception:
            pass
        yield f"data: {error_msg}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        logger.error(f"[{request_id}] 调用服务失败: {str(e)}")
        logger.exception(e)
        yield f"data: 服务暂时不可用: {str(e)}\n\n"
        yield "data: [DONE]\n\n"


@agentController.get("/chat")
async def chat_with_agent(
        request: Request,
        message: str = Query(..., description="用户消息"),
        deep_thinking: Optional[bool] = Query(default=False, alias="deepThinking", description="是否启用深度思考模式"),
        chat_id: Optional[str] = Query(default=None, alias="sessionChatId",
                                       description="会话级 chatId，来自前端 localStorage（可选）"),
        token_param: Optional[str] = Query(default=None, description="可选token参数"),
        query_db: Session = Depends(get_db),
):
    """
    根据 deep_thinking 参数选择上游 endpoint。
    deep_thinking=True -> 深度思考 (liteMind)
    deep_thinking=False -> 简单对话 (simple)
    """
    request_id = uuid4().hex
    try:
        if not message or not message.strip():
            return ResponseUtil.error(msg='消息内容不能为空')

        # 如果前端传入 chat_id，则做简单校验并注册（记录）
        if chat_id:
            try:
                # 要求为 uuid4().hex 格式的 32 位十六进制字符串
                if not (isinstance(chat_id, str) and len(chat_id) == 32 and int(chat_id, 16) >= 0):
                    logger.warning(f"[{request_id}] 无效的 chat_id: {chat_id}")
                    return ResponseUtil.error(msg="invalid chat_id")
            except Exception:
                logger.warning(f"[{request_id}] 无效的 chat_id(format): {chat_id}")
                return ResponseUtil.error(msg="invalid chat_id")
            # 简单注册：记录日志（未来可扩展为持久化）
            logger.info(f"[{request_id}] chat_id accepted/registered: {chat_id}")
        # 如果前端传入 chat_id，则将其转发给 Agent 作为 chatId；
        # 否则不主动生成或传递 chatId，让 Agent 自行生成并在 SSE 流中下发 __CHAT_ID__ 给前端。
        params = {"message": message}
        if chat_id:
            params["chatId"] = chat_id  # 已在上面校验格式并记录

        # choose endpoint
        if deep_thinking:
            endpoint = AgentConfig.DEEP_THINKING_ENDPOINT
            label = "deep thinking"
        else:
            endpoint = AgentConfig.SIMPLE_CHAT_ENDPOINT
            label = "simple chat"
        agent_url = f"{AgentConfig.LITEMIND_AGENT_BASE_URL}{endpoint}"

        # 解析用户和token
        result = await parse_cur_user_and_token(request, request_id, token_param, query_db)
        if result is None:
            return ResponseUtil.unauthorized(msg='认证失败或已过期，请重新登录')
        user_name, token = result

        logger.info(
            f"[{request_id}] 转发{label}SSE请求到LiteMind-Agent服务: {agent_url}, 用户: {user_name}, "
            f"message_preview: {message[:50]}..., provided_chat_id: {chat_id or '<none>'}")

        # 返回SSE流式响应
        return StreamingResponse(
            stream_agent_response(agent_url, params, token, request_id, label),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
            }
        )
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=f'处理请求时出错: {str(e)}')


@agentController.post("/terminate")
async def terminate_agent_chat(
        request: Request,
        chat_id: str = Query(..., description="要终止的chatId"),
        token_param: Optional[str] = Query(default=None, description="可选token参数"),
):
    """
    转发终止请求到 Agent 服务
    """
    request_id = uuid4().hex
    try:
        token = token_param or request.query_params.get('token') or request.headers.get('Authorization', '').replace(
            'Bearer ', '')
        terminate_url = f"{AgentConfig.LITEMIND_AGENT_BASE_URL}{AgentConfig.TERMINATE_ENDPOINT}"

        async with AsyncClient(timeout=AgentConfig.LITEMIND_AGENT_TIMEOUT,
                               trust_env=trust_env_proxy(terminate_url)) as client:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            # 使用 POST 方式通知 Agent 终止指定 chatId
            resp = await client.post(terminate_url, params={"chatId": chat_id}, headers=headers)
            try:
                raw = await resp.aread()
                raw_text = raw.decode('utf-8', errors='replace').strip()
            except Exception:
                raw_text = ""

            # 如果 Agent 返回 HTTP 404，明确映射为 app-level 404 响应（chatId 未找到）
            if resp.status_code == 404:
                logger.warning(f"[{request_id}] Agent terminate returned 404 for chatId: {chat_id}, body: {raw_text}")
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=jsonable_encoder({
                        "code": 404,
                        "msg": "chatId not found",
                        "success": False,
                        "time": datetime.now()
                    })
                )

            # try parse JSON body
            if raw_text:
                try:
                    parsed = loads(raw_text)
                    result_value = parsed.get("result") or parsed.get("status") or parsed.get("code")
                    if isinstance(result_value, int):
                        result_value = str(result_value)
                except Exception:
                    result_value = raw_text
            else:
                result_value = ""

            rv = (result_value or "").strip().lower()

            if resp.status_code == 200 and rv in ("terminated", "ok", "done", "success"):
                logger.info(
                    f"[{request_id}] 已转发终止请求到 Agent: {terminate_url}, chatId: {chat_id}, result: {result_value}")
                return ResponseUtil.success(msg="terminate forwarded")
            elif resp.status_code == 200 and rv in ("not_found", "notfound", "404"):
                logger.warning(f"[{request_id}] 终止请求返回 not_found for chatId: {chat_id}")
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=jsonable_encoder({
                        "code": 404,
                        "msg": "chatId not found",
                        "success": False,
                        "time": datetime.now()
                    })
                )
            else:
                logger.error(f"[{request_id}] 转发终止请求失败: {resp.status_code}, body: {raw_text}")
                return ResponseUtil.error(msg=f"terminate failed, status {resp.status_code}")
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=f"terminate failed: {str(e)}")
