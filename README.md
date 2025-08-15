Deadcat Recoder
================

목차
------------
1. 프로젝트 구조
2. 


### 1. 프로젝트 구조

```
deadcat-recorder/
├── src/
│   ├── main.py                 # 메인 진입점
│   ├── config.py               # 전역 설정
│   ├── game.py                 # 게임 메인 클래스
│   │
│   ├── core/                   # 핵심 시스템
│   │   ├── __init__.py
│   │   ├── state_manager.py    # 상태 관리
│   │   ├── scene_manager.py    # 씬 전환 관리
│   │   ├── event_system.py     # 이벤트 시스템
│   │   └── resource_loader.py  # 리소스 로딩
│   │
│   ├── inputs/                 # 입력 처리
│   │   ├── __init__.py
│   │   ├── hardware_input.py   # GPIO 입력
│   │   └── input_mapper.py     # 입력 매핑
│   │
│   ├── audio/                  # 오디오 처리
│   │   ├── __init__.py
│   │   ├── recorder.py         # 녹음 기능
│   │   ├── player.py           # 재생 기능
│   │   ├── processor.py        # 오디오 처리 (trim, reverse 등)
│   │   └── loop_engine.py      # 루프 재생 엔진
│   │
│   ├── scenes/                 # 씬 구현
│   │   ├── __init__.py
│   │   ├── base_scene.py       # 씬 베이스 클래스
│   │   ├── bridge_scene.py     # Bridge 씬
│   │   ├── work_lane/
│   │   │   ├── __init__.py
│   │   │   ├── recording_scene.py
│   │   │   ├── sound_crafting_scene.py
│   │   │   └── loop_composition_scene.py
│   │   └── library_lane/
│   │       ├── __init__.py
│   │       └── library_scene.py
│   │
│   ├── models/                 # 데이터 모델
│   │   ├── __init__.py
│   │   ├── sample.py           # Sample 모델
│   │   ├── sound_stone.py      # SoundStone 모델
│   │   ├── loop.py             # Loop 모델
│   │   └── tail_pack.py        # TailPack 모델
│   │
│   ├── ui/                     # UI 컴포넌트
│   │   ├── __init__.py
│   │   ├── components.py       # 공통 UI 컴포넌트
│   │   ├── animations.py       # 애니메이션
│   │   └── visual_elements.py  # 시각적 요소
│   │
│   └── utils/                  # 유틸리티
│       ├── __init__.py
│       ├── file_manager.py     # 파일 저장/로드
│       └── constants.py        # 상수 정의
│
├── assets/                     # 리소스
│   ├── images/
│   ├── sounds/
│   └── fonts/
│
├── data/                       # 사용자 데이터
│   ├── samples/               # 녹음된 샘플
│   ├── loops/                 # 제작된 루프
│   └── library/               # 라이브러리 데이터
│
└── run_game.sh
```