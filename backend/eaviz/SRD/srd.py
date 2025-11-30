from eaviz.SRD.hfo import hfo_process


class SRD:
    """
    SRD分析类
    """

    @staticmethod
    def srd(raw, model, start_time, stop_time, ch_idx):
        raw.load_data()
        merged_raw = hfo_process(raw, model, ch_idx, start_time, stop_time)
