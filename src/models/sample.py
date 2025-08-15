# ============================================
# models/sample.py - 데이터 모델
# ============================================
"""샘플 데이터 모델"""

class Sample:
    def __init__(self, audio_data, sample_rate, name=None):
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.name = name or "Untitled Sample"
        self.duration = len(audio_data) / sample_rate if audio_data else 0
        self.metadata = {}
    
    def trim(self, start, end):
        """샘플 트림"""
        start_sample = int(start * self.sample_rate)
        end_sample = int(end * self.sample_rate)
        self.audio_data = self.audio_data[start_sample:end_sample]
        self.duration = len(self.audio_data) / self.sample_rate
    
    def reverse(self):
        """샘플 역재생"""
        self.audio_data = self.audio_data[::-1]
    
    def change_speed(self, factor):
        """속도 변경"""
        # TODO: 적절한 리샘플링 구현
        pass

class SoundStone:
    """AI 처리된 소리 원석"""
    def __init__(self, sample, visual_properties):
        self.sample = sample
        self.visual_properties = visual_properties
        self.color = None
        self.shape = None
        self.texture = None
    
    def apply_tool(self, tool_name, parameters):
        """도구 적용"""
        if tool_name == "trim":
            self.sample.trim(parameters["start"], parameters["end"])
        elif tool_name == "reverse":
            self.sample.reverse()
        # ... 기타 도구들

class Loop:
    """루프 (완성된 꼬리)"""
    def __init__(self, bpm=120, bars=4):
        self.bpm = bpm
        self.bars = bars
        self.layers = [[] for _ in range(4)]  # 4 레이어
        self.sound_stones = []
    
    def add_stone_to_layer(self, layer_idx, bar_position, sound_stone):
        """레이어에 소리 원석 추가"""
        if 0 <= layer_idx < 4:
            self.layers[layer_idx].append({
                "position": bar_position,
                "stone": sound_stone
            })
    
    def export_as_tail_pack(self):
        """TailPack으로 export"""
        return TailPack(self)

class TailPack:
    """Export 가능한 샘플팩"""
    def __init__(self, loop):
        self.loop = loop
        self.name = f"Tail_{id(self)}"
        self.created_date = None
        self.exported = False
    
    def export(self, format="wav"):
        """실제 파일로 export"""
        # TODO: 파일 생성 로직
        self.exported = True
        return f"{self.name}.{format}"