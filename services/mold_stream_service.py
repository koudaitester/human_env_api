import time
from collections import deque
from typing import Dict, Optional, Any
from services.log_service import logger
from services.mold_weight_service import calc_mold_weight_result
from services.moondream_service import moondream_service
import base64
from utils.rag_helper import get_rag_knowledge


class MoldStreamService:
    def __init__(self):
        self.window_size = 5
        self.window = deque(maxlen=self.window_size)
        self.latest_vote: Optional[Dict[str, Any]] = None

    async def feed_frame(self, img_b64: str):
        try:
            vision_resp = await moondream_service.analyze_mold_visual(img_b64)
            img_struct = vision_resp["data"]
            rule_txt = await get_rag_knowledge("mold_risk_calc.md")
            risk_result = calc_mold_weight_result(img_struct, None, None, rule_txt)
            level = risk_result["riskLevel"]
            self.window.append(level)
            logger.info(f"stream feed frame, level={level}, window={list(self.window)}")

            if len(self.window) >= self.window_size:
                self.latest_vote = self._vote()
            return risk_result
        except Exception as e:
            logger.exception("feed frame error")
            raise e

    def _vote(self) -> Dict[str, Any]:
        level_list = list(self.window)
        vote_level = max(set(level_list), key=level_list.count)
        return {
            "window": level_list,
            "vote_result": vote_level
        }

    def get_latest_vote(self) -> Optional[Dict[str, Any]]:
        return self.latest_vote

    def clear_window(self):
        self.window.clear()
        self.latest_vote = None
        logger.info("window cleared")


mold_stream_service = MoldStreamService()
