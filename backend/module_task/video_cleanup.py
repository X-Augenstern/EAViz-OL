from datetime import datetime, timezone, timedelta
from json import loads
from os import path, remove, walk
from redis import Redis

from config.env import RedisConfig, RedisInitKeyConfig, EAVizConfig
from config.get_db import get_db_context
from config.get_redis import RedisUtil
from module_admin.entity.vo.video_vo import DeleteVideoModel
from module_admin.service.video_service import VideoService
from utils.log_util import logger


def _get_redis_client() -> Redis:
    # 使用全局连接池避免定时任务频繁建连
    return RedisUtil.get_sync_redis_client()


def _parse_expire_at(expire_at_str: str):
    """
    将 ISO 格式的过期时间安全解析为 UTC 时间
    """
    if not expire_at_str:
        return None
    try:
        # payload 中存储的是带时区信息的 ISO 字符串
        parsed = datetime.fromisoformat(expire_at_str)
        # 确保返回的时间是UTC时区的可比较时间
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception as exc:
        logger.warning(f"视频清理任务解析过期时间失败: {expire_at_str}, 错误: {exc}")
        return None


def _cleanup_files_by_mtime(base_dir: str, expire_before: datetime):
    """
    兜底扫描指定目录，删除修改时间早于 expire_before 的文件
    """
    if not base_dir or not path.exists(base_dir):
        return
    removed = 0
    # os.walk(base_dir) 会从 base_dir 开始，深度优先 / 广度优先（默认深度优先） 遍历所有子目录，每次迭代返回三个值：
    # root：当前正在遍历的目录路径（比如 base_dir/a/b）
    # dirs：当前 root 目录下的子目录列表（不含孙子目录，仅一级）
    # files：当前 root 目录下的文件列表（不含子目录里的文件，仅一级）
    # 因此，最终会覆盖 base_dir 下所有层级的所有文件（不管有多少层子目录，里面的文件都会被获取到）
    for root, _, files in walk(base_dir):
        for fname in files:
            fpath = path.join(root, fname)
            try:
                mtime = datetime.fromtimestamp(path.getmtime(fpath), tz=timezone.utc)
                if mtime < expire_before:
                    remove(fpath)
                    removed += 1
            except Exception as exc:
                logger.warning(f"兜底清理目录文件失败: {fpath}, 错误: {exc}")
    if removed:
        logger.info(f"处理后视频兜底清理完成，按修改时间删除文件 {removed} 个")


def job():
    """
    定期扫描Redis记录，删除已过期或缺失的处理后视频
    """
    client = _get_redis_client()
    removed_files = 0
    deleted_keys = 0
    cursor = 0
    now_utc = datetime.now(timezone.utc)
    video_id_list = []
    try:
        while True:
            cursor, keys = client.scan(cursor=cursor, match=f"{RedisInitKeyConfig.VIDEO_CLEANUP.get('key')}:*",
                                       count=200)
            for key in keys:
                try:
                    key_parts = key.split(":")
                    key_video_id = key_parts[-1] if len(key_parts) >= 2 else None
                    data = client.get(key)
                    if not data:
                        client.delete(key)
                        deleted_keys += 1
                        continue

                    payload = loads(data)
                    expire_at = _parse_expire_at(payload.get("expire_at"))
                    # 未过期且有有效到期时间则跳过
                    if expire_at and expire_at > now_utc:
                        continue
                    file_path = payload.get("path")
                    video_id = payload.get("video_id") or key_video_id
                    if video_id is not None:
                        video_id_list.append(video_id)

                    # 删除本地文件
                    if file_path and path.exists(file_path):
                        try:
                            remove(file_path)
                            removed_files += 1
                            logger.info(f"已删除过期视频: video_id={video_id}, path={file_path}")
                        except Exception as exc:
                            logger.warning(f"删除过期视频失败: video_id={video_id}, path={file_path}, 错误: {exc}")
                    else:
                        if video_id:
                            logger.debug(f"视频文件不存在/路径为空: video_id={video_id}, path={file_path}")

                    # 清理Redis记录
                    client.delete(key)
                    deleted_keys += 1
                except Exception as row_exc:
                    logger.warning(f"处理过期视频清理记录失败: key={key}, 错误: {row_exc}")
            if cursor == 0:
                break

        # 同步删除数据库中的视频记录及用户关联记录
        if len(video_id_list) > 0:
            delete_video = DeleteVideoModel(videoIds=",".join(map(str, video_id_list)))
            # 2025-12-10 15:14:00.032 | ERROR    | module_task.video_cleanup:job:134 - 视频清理任务执行异常: 'generator' object has no attribute 'rollback'
            # delete_video_result = VideoService.delete_video_services(get_db(), delete_video)

            # 核心原因：Depends 的「魔法」只在请求上下文生效
            # 接口里用 Depends(get_db) 能正常工作，是因为 FastAPI 会自动解析生成器函数（get_db_pro）：
            # Depends 会调用 get_db_pro() 拿到生成器，再执行 next(生成器) 获取 yield 返回的 Session 实例；
            # 接口请求结束后，FastAPI 还会自动触发生成器的 finally 逻辑（关闭 Session）；
            # 但定时任务运行在「无请求上下文」的线程中，没有 Depends 这个解析逻辑，直接调用 get_db() 只能拿到「生成器对象」，而非 Session 实例，所以调用 query()/rollback() 会报错。

            # 解决方案：手动封装「上下文管理器」适配定时任务
            # 需要手动模拟 Depends 的逻辑 —— 解析生成器、获取 Session、保证最终关闭，用 contextlib 封装成「上下文管理器」（和 with 语法配合，安全又简洁）。

            """
            为什么用上下文管理器？
                with get_db_context() 会自动触发：
                进入时：解析生成器 → 获取 Session；
                退出时：触发生成器的 finally → 关闭 Session；
                异常时：自动回滚 + 关闭 Session，和接口的 Depends 行为完全对齐。
            异步 vs 同步？
                get_db_pro 是同步的（基于 SessionLocal），定时任务也用同步逻辑即可；
                如果项目是异步 SQLAlchemy（AsyncSession），只需把 get_db_context 改成 async contextmanager，with 改成 async with。
            线程安全？
                SessionLocal() 是「每个请求 / 每个定时任务线程创建一个 Session」，天然线程安全，无需担心。
            最终效果
                定时任务中通过 with get_db_context() as db_session 获取的是真正的 Session 实例，而非生成器
                调用 query()/rollback()/commit() 都能正常工作，和接口的数据库操作逻辑完全一致。
            """
            with get_db_context() as db_session:
                delete_video_result = VideoService.delete_video_services(db_session, delete_video)
            if delete_video_result.is_success:
                if removed_files != len(video_id_list):
                    logger.warning(
                        f"成功删除数据库中 {len(video_id_list)} 条过期视频记录，但与本地删除的文件数量 {removed_files} 不一致")
                else:
                    logger.info(f"成功删除数据库中 {len(video_id_list)} 条过期视频记录：{delete_video_result.message}")
            else:
                logger.warning(f"删除数据库视频记录失败：{delete_video_result.message}")

        if removed_files or deleted_keys:
            logger.info(
                f"过期视频清理完成，删除文件 {removed_files} 个，清理Redis记录 {deleted_keys} 条")

        # 兜底：按文件修改时间扫描视频所在目录，清理超出TTL的残留文件（防止Redis键丢失导致无法清理）
        _cleanup_files_by_mtime(
            base_dir=EAVizConfig.AddressConfig.get_vd_adr("res"),
            expire_before=now_utc - timedelta(seconds=RedisConfig.video_file_ttl_seconds)
        )
    except Exception as exc:
        logger.exception(f"视频清理任务执行异常: {exc}")
    finally:
        client.close()
