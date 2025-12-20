from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import StreamingResponse
from httpx import AsyncClient, TimeoutException, HTTPStatusError, Limits
from sqlalchemy.orm import Session
from typing import Optional
from uuid import uuid4

from config.env import AgentConfig
from config.get_db import get_db
from module_admin.service.login_service import LoginService
from utils.log_util import *
from utils.response_util import ResponseUtil

# 取消全局依赖，便于从 query/header 中自行解析 token
agentController = APIRouter(prefix='/agent')


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


def extract_content(msg: str) -> str:
    """提取SSE消息的实际内容，去掉data:前缀"""
    if not msg:
        return ""
    # 提取data字段的实际内容（支持 "data: " 和 "data:" 两种格式）
    if msg.startswith('data: '):
        return msg[6:].strip()  # 去掉 "data: " 前缀
    elif msg.startswith('data:'):
        return msg[5:].strip()  # 去掉 "data:" 前缀
    else:
        return msg.strip()


async def stream_agent_response(
        agent_url: str,
        params: dict,
        token: Optional[str],
        request_id: str,
        log_prefix: str = "Agent"
):
    """通用的SSE流式响应生成器"""
    try:
        # 使用httpx异步客户端调用Agent服务，配置连接池限制
        async with AsyncClient(
                timeout=AgentConfig.LITEMIND_AGENT_TIMEOUT,
                limits=Limits(max_keepalive_connections=5, max_connections=10)
        ) as client:
            # 发送GET请求，接收SSE流
            headers = {
                "Accept": "text/event-stream",
            }
            # 如果Agent需要认证，可以传递token
            if token:
                headers["Authorization"] = f"Bearer {token}"

            async with client.stream(
                    'GET',
                    agent_url,
                    params=params,
                    headers=headers
            ) as response:
                # 检查HTTP状态码
                if response.status_code != 200:
                    error_msg = f"Agent服务返回错误状态码: {response.status_code}"
                    logger.error(f"[{request_id}] {error_msg}")
                    yield f"data: {error_msg}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                # 直接按文本读取，让httpx处理编码
                buffer = ""

                async for chunk in response.aiter_text():
                    if not chunk:
                        continue

                    buffer += chunk

                    # 处理完整的SSE消息（以\n\n结尾）
                    while '\n\n' in buffer:
                        msg_end = buffer.find('\n\n')
                        msg = buffer[:msg_end].strip()
                        buffer = buffer[msg_end + 2:]

                        if not msg:
                            continue

                        # 提取实际内容（去掉data:前缀）
                        content = extract_content(msg)
                        if not content:
                            continue

                        # 发送实际内容，保持SSE格式
                        if msg.startswith('event:') or msg.startswith('id:'):
                            # 其他SSE字段（虽然Java端不发送，但保留兼容性）
                            yield f"{msg}\n"
                        elif msg.startswith(':'):
                            # 注释行，跳过
                            continue
                        else:
                            # 发送实际内容（已去掉data:前缀）
                            yield f"data: {content}\n\n"

                # 处理流结束时的剩余buffer
                if buffer.strip():
                    remaining = buffer.strip()
                    # 提取实际内容（去掉data:前缀）
                    content = extract_content(remaining)
                    if content:
                        # 发送实际内容，保持SSE格式
                        yield f"data: {content}\n\n"

                # 发送结束标记
                yield "data: [DONE]\n\n"
                logger.info(f"[{request_id}] {log_prefix}SSE流式响应完成")

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


@agentController.get("/chat/liteMind")
async def chat_with_agent(
        request: Request,
        message: str = Query(..., description="用户消息"),
        token_param: Optional[str] = Query(default=None, description="可选token参数"),
        query_db: Session = Depends(get_db),
):
    """
    SSE流式代理到LiteMind-Agent服务的深度思考接口
    
    使用GET请求，参数：
    - message: 用户消息内容
    
    返回SSE流式响应
    """
    request_id = str(uuid4())[:8]

    try:
        if not message or not message.strip():
            return ResponseUtil.error(msg='消息内容不能为空')

        # 构建LiteMind-Agent服务URL（使用GET请求）
        agent_url = f"{AgentConfig.LITEMIND_AGENT_BASE_URL}{AgentConfig.DEEP_THINKING_ENDPOINT}"
        params = {"message": message}

        # 解析用户和token
        result = await parse_cur_user_and_token(request, request_id, token_param, query_db)
        if result is None:
            return ResponseUtil.error(code=401, msg='认证失败或已过期，请重新登录')
        user_name, token = result

        logger.info(
            f"[{request_id}] 转发深度思考SSE请求到LiteMind-Agent服务: {agent_url}, "
            f"用户: {user_name}, 消息: {message[:50]}..."
        )

        # 返回SSE流式响应
        return StreamingResponse(
            stream_agent_response(agent_url, params, token, request_id, "deep thinking"),
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


@agentController.get("/chat/simple")
async def simple_chat_with_agent(
        request: Request,
        message: str = Query(..., description="用户消息"),
        chat_id: Optional[str] = Query(default=None, description="会话ID，可选"),
        token_param: Optional[str] = Query(default=None, description="可选token参数"),
        query_db: Session = Depends(get_db),
):
    """
    SSE流式代理到LiteMind-Agent服务的简单对话接口
    
    使用GET请求，参数：
    - message: 用户消息内容
    - chat_id: 会话ID（可选，默认使用"default"）
    
    返回SSE流式响应
    """
    request_id = str(uuid4())[:8]

    try:
        if not message or not message.strip():
            return ResponseUtil.error(msg='消息内容不能为空')

        # 如果没有提供chatId，使用默认值
        if not chat_id or not chat_id.strip():
            chat_id = "default"

        # 构建LiteMind-Agent服务URL（使用GET请求）
        agent_url = f"{AgentConfig.LITEMIND_AGENT_BASE_URL}{AgentConfig.SIMPLE_CHAT_ENDPOINT}"
        params = {"message": message, "chatId": chat_id}

        # 解析用户和token
        result = await parse_cur_user_and_token(request, request_id, token_param, query_db)
        if result is None:
            return ResponseUtil.error(code=401, msg='认证失败或已过期，请重新登录')
        user_name, token = result

        logger.info(
            f"[{request_id}] 转发简单对话SSE请求到LiteMind-Agent服务: {agent_url}, "
            f"用户: {user_name}, 会话ID: {chat_id}, 消息: {message[:50]}..."
        )

        # 返回SSE流式响应
        return StreamingResponse(
            stream_agent_response(agent_url, params, token, request_id, "simple chat"),
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
